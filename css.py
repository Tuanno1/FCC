import os
import time
import pandas as pd
import soundfile as sf
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from gradio_client import Client
from tqdm import tqdm
from datetime import timedelta
import threading
import shutil

# ================== CONFIG ==================
GRADIO_URL = "http://192.168.2.11:7901/"
VOICE = "vn_man_male"

BIBLE_DIR = "D:/project ASR/Fine-tune ASR/1925"
TXT_FILES = [
    os.path.join(BIBLE_DIR, "vtt_ot.txt"),
    os.path.join(BIBLE_DIR, "vtt_nt.txt")
]

OUTPUT_DIR = os.path.join(BIBLE_DIR, f"dataset_{VOICE}")
CLIP_DIR = os.path.join(OUTPUT_DIR, "clips")
TRAIN_CSV = os.path.join(OUTPUT_DIR, "train.csv")
FAILED_TXT = os.path.join(OUTPUT_DIR, "failed.txt")
BACKUP_DIR = os.path.join(OUTPUT_DIR, "backups")

BATCH_SIZE = 50
MAX_WORKERS = 8
START_INDEX = 0
CHECKPOINT_INTERVAL = 10

# ASR Quality Requirements
TARGET_SR = 16000
MIN_DURATION = 0.5
MAX_DURATION = 30.0
MIN_RMS = 0.01
MAX_RETRIES = 3

# ============================================
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Thread-safe collections
csv_lock = threading.Lock()
pending_rows = []

# ---------- Connect to Gradio API ----------
print(f"🔌 Connecting to Gradio API at {GRADIO_URL}...")
try:
    global_client = Client(GRADIO_URL)
    print("✅ Connected successfully")
    
    # Validate API endpoint
    try:
        test_result = global_client.predict(
            text="test",
            output_file="",
            TRANSLATE_AUDIO_TO="Vietnamese (vi)",
            tts_voice=VOICE,
            speed=1.0,
            desired_duration="",
            start_time="",
            t2s_method="VietTTS",
            api_name="/tts"
        )
        print("✅ API endpoint validated")
    except Exception as e:
        print(f"⚠️  Warning: API test failed: {e}")
        print("   Continuing anyway, but may fail during generation...")
        
except Exception as e:
    print(f"❌ Cannot connect to {GRADIO_URL}: {e}")
    print("   Please check:")
    print("   1. Gradio server is running at 192.168.2.11:7901")
    print("   2. Network connection")
    print("   3. Firewall settings")
    exit(1)

# ---------- Load existing metadata ----------
if os.path.exists(TRAIN_CSV):
    try:
        train_df = pd.read_csv(TRAIN_CSV)
        required_cols = ['path', 'text', 'duration']
        if not all(col in train_df.columns for col in required_cols):
            print(f"⚠️  Warning: CSV missing columns, recreating...")
            train_df = pd.DataFrame(columns=required_cols)
            existing_files = set()
            start_id = 0
        else:
            existing_files = set(train_df['path'].str.replace('clips/', '').tolist())
            start_id = len(train_df)
            print(f"📂 Found {len(train_df)} existing samples")
    except Exception as e:
        print(f"⚠️  Warning: Cannot read CSV: {e}")
        train_df = pd.DataFrame(columns=["path", "text", "duration"])
        existing_files = set()
        start_id = 0
else:
    train_df = pd.DataFrame(columns=["path", "text", "duration"])
    existing_files = set()
    start_id = 0

# ---------- Load text from VTT files ----------
def parse_vtt_line(line):
    """Parse line format: timestamp|text"""
    if '|' in line:
        parts = line.split('|', 1)
        if len(parts) == 2:
            return parts[1].strip()
    return None

all_texts = []
print(f"📖 Loading texts from VTT files...")

for txt_file in TXT_FILES:
    if not os.path.exists(txt_file):
        print(f"⚠️  Warning: File not found: {txt_file}")
        continue
    
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                text = parse_vtt_line(line)
                if text and len(text) > 5:
                    all_texts.append(text)
        print(f"   ✓ {os.path.basename(txt_file)}: {len([t for t in all_texts])} lines")
    except Exception as e:
        print(f"   ✗ Error reading {txt_file}: {e}")

if not all_texts:
    print(f"❌ Error: No valid texts found in VTT files!")
    exit(1)

all_texts = all_texts[START_INDEX:]
print(f"📝 Total texts to process: {len(all_texts):,}")
print(f"🎯 Starting from ID: {start_id:06d}")

# ---------- Audio validation ----------
def validate_audio(wav_path):
    """Validate audio quality for ASR"""
    try:
        data, sr = sf.read(wav_path)
        
        # Convert stereo to mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        duration = len(data) / sr
        
        # Check duration
        if duration < MIN_DURATION or duration > MAX_DURATION:
            return False, f"Duration {duration:.2f}s out of range"
        
        # Check RMS (silence detection)
        rms = np.sqrt(np.mean(data**2))
        if rms < MIN_RMS:
            return False, f"RMS too low {rms:.4f} (silence?)"
        
        # Resample to 16kHz if needed
        if sr != TARGET_SR:
            try:
                from scipy import signal
                num_samples = int(len(data) * TARGET_SR / sr)
                data = signal.resample(data, num_samples)
                sf.write(wav_path, data, TARGET_SR)
            except ImportError:
                try:
                    import librosa
                    data = librosa.resample(data, orig_sr=sr, target_sr=TARGET_SR)
                    sf.write(wav_path, data, TARGET_SR)
                except ImportError:
                    print("⚠️  Warning: Neither scipy nor librosa available, keeping original SR")
        
        return True, duration
        
    except Exception as e:
        return False, str(e)

# ---------- TTS function ----------
def generate_audio(args):
    """Generate single audio file"""
    file_id, text = args
    filename = f"{file_id:06d}.wav"
    wav_path = os.path.join(CLIP_DIR, filename)
    
    # Skip if exists and valid
    if filename in existing_files and os.path.exists(wav_path):
        try:
            valid, duration = validate_audio(wav_path)
            if valid and isinstance(duration, float):
                return (filename, text, duration, "existed")
            else:
                os.remove(wav_path)
        except Exception:
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
    
    # Generate with retry
    for attempt in range(MAX_RETRIES):
        try:
            result = global_client.predict(
                text=text,
                output_file="",
                TRANSLATE_AUDIO_TO="Vietnamese (vi)",
                tts_voice=VOICE,
                speed=1.0,
                desired_duration="",
                start_time="",
                t2s_method="VietTTS",
                api_name="/tts"
            )
            
            audio_file = result if isinstance(result, str) else (result[0] if result else None)
            
            # Move file
            if audio_file and os.path.exists(audio_file):
                try:
                    os.replace(audio_file, wav_path)
                except Exception:
                    shutil.copy2(audio_file, wav_path)
                    try:
                        os.remove(audio_file)
                    except:
                        pass
            else:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                else:
                    return (filename, text, None, "error: no output file")
            
            # Validate
            valid, duration = validate_audio(wav_path)
            
            if valid:
                return (filename, text, duration, "success")
            else:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                if attempt == MAX_RETRIES - 1:
                    return (filename, text, None, f"invalid: {duration}")
                time.sleep(1)
                
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return (filename, text, None, f"error: {str(e)[:100]}")
            time.sleep(1)
    
    return (filename, text, None, "failed")

# ---------- Batch CSV writer ----------
def flush_pending_rows():
    """Ghi tất cả pending rows vào CSV 1 lần"""
    global train_df, pending_rows
    
    with csv_lock:
        if pending_rows:
            new_data = pd.DataFrame(pending_rows)
            train_df = pd.concat([train_df, new_data], ignore_index=True)
            train_df.to_csv(TRAIN_CSV, index=False)
            
            for row in pending_rows:
                filename = row['path'].replace('clips/', '')
                existing_files.add(filename)
            
            pending_rows.clear()

def queue_csv_row(filename, text, duration):
    """Thêm row vào queue"""
    with csv_lock:
        pending_rows.append({
            "path": f"clips/{filename}",
            "text": text,
            "duration": duration
        })

def backup_csv(batch_num):
    """Backup CSV periodically"""
    try:
        if os.path.exists(TRAIN_CSV):
            backup_name = f"train_backup_batch_{batch_num:04d}.csv"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            shutil.copy2(TRAIN_CSV, backup_path)
            
            backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("train_backup")])
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    try:
                        os.remove(os.path.join(BACKUP_DIR, old_backup))
                    except:
                        pass
    except Exception as e:
        print(f"⚠️  Warning: Backup failed: {e}")

# ---------- Main loop ----------
failed = []
stats = {
    'success': 0,
    'failed': 0,
    'existed': 0,
    'total_duration': 0,
    'actual_processed': 0
}

start_time = time.time()

print(f"\n{'='*60}")
print("🚀 STARTING DATASET GENERATION")
print(f"{'='*60}")
print(f"🎤 Voice: {VOICE}")
print(f"💾 Output: {OUTPUT_DIR}")
print(f"{'='*60}\n")

try:
    for batch_idx in range(0, len(all_texts), BATCH_SIZE):
        batch_end = min(batch_idx + BATCH_SIZE, len(all_texts))
        batch_texts = all_texts[batch_idx:batch_end]
        
        batch_num = batch_idx // BATCH_SIZE + 1
        total_batches = (len(all_texts) - 1) // BATCH_SIZE + 1
        
        print(f"\n📦 Batch {batch_num}/{total_batches} "
              f"(Files {start_id + batch_idx:06d} - {start_id + batch_end - 1:06d})")
        
        # Prepare tasks
        tasks = [
            (start_id + batch_idx + i, text) 
            for i, text in enumerate(batch_texts)
        ]
        
        # Execute in parallel
        batch_stats = {'success': 0, 'existed': 0, 'failed': 0}
        futures = {}
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for task in tasks:
                future = executor.submit(generate_audio, task)
                futures[future] = task
            
            # Process results with progress bar
            with tqdm(total=len(futures), desc="Processing", ncols=100) as pbar:
                for future in as_completed(futures):
                    try:
                        filename, text, duration, status = future.result()
                        
                        if status == "success":
                            queue_csv_row(filename, text, duration)
                            stats['success'] += 1
                            stats['actual_processed'] += 1
                            stats['total_duration'] += duration
                            batch_stats['success'] += 1
                            
                        elif status == "existed":
                            if filename not in existing_files:
                                queue_csv_row(filename, text, duration)
                            stats['existed'] += 1
                            stats['total_duration'] += duration
                            batch_stats['existed'] += 1
                            
                        else:
                            failed.append(f"{filename}|{text}|{status}")
                            stats['failed'] += 1
                            stats['actual_processed'] += 1
                            batch_stats['failed'] += 1
                        
                        pbar.set_postfix({
                            '✓': batch_stats['success'], 
                            '✗': batch_stats['failed'],
                            '⊙': batch_stats['existed']
                        })
                        pbar.update(1)
                        
                    except Exception as e:
                        print(f"\n⚠️  Error processing future: {e}")
                        stats['failed'] += 1
                        batch_stats['failed'] += 1
                        pbar.update(1)
        
        # Flush CSV sau mỗi batch
        flush_pending_rows()
        
        # Backup CSV periodically
        if batch_num % CHECKPOINT_INTERVAL == 0:
            backup_csv(batch_num)
            print(f"💾 Checkpoint saved (batch {batch_num})")
        
        # Save failed periodically
        if failed and (batch_num % 5 == 0):
            with open(FAILED_TXT, "a", encoding="utf-8") as f:
                for line in failed:
                    f.write(line + "\n")
            failed.clear()
        
        # ETA calculation
        current_time = time.time()
        elapsed = current_time - start_time
        
        if stats['actual_processed'] > 0:
            total_to_process = len(all_texts)
            already_done = batch_idx + len(batch_texts)
            remaining = total_to_process - already_done
            
            avg_time_per_file = elapsed / stats['actual_processed']
            
            if already_done > 0:
                existed_ratio = stats['existed'] / already_done
                estimated_new_files = remaining * (1 - existed_ratio)
                eta_seconds = avg_time_per_file * estimated_new_files
            else:
                eta_seconds = avg_time_per_file * remaining
            
            speed = stats['actual_processed'] / elapsed if elapsed > 0 else 0
            
            print(f"⏱️  Elapsed: {timedelta(seconds=int(elapsed))} | "
                  f"ETA: {timedelta(seconds=int(eta_seconds))} | "
                  f"Speed: {speed:.2f} files/s")
            print(f"📊 Progress: {already_done}/{total_to_process} texts "
                  f"({already_done/total_to_process*100:.1f}%) | "
                  f"✓ {stats['success']} | ✗ {stats['failed']} | ⊙ {stats['existed']}")
        else:
            print(f"⏱️  Elapsed: {timedelta(seconds=int(elapsed))}")

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user (Ctrl+C)")
    print("💾 Saving progress...")
    flush_pending_rows()
    if failed:
        with open(FAILED_TXT, "a", encoding="utf-8") as f:
            for line in failed:
                f.write(line + "\n")
    print("✅ Progress saved. You can resume later.")
    exit(0)

except Exception as e:
    print(f"\n\n❌ Unexpected error: {e}")
    print("💾 Attempting to save progress...")
    try:
        flush_pending_rows()
        if failed:
            with open(FAILED_TXT, "a", encoding="utf-8") as f:
                for line in failed:
                    f.write(line + "\n")
        print("✅ Progress saved")
    except:
        print("❌ Cannot save progress")
    raise

# ---------- Final flush ----------
flush_pending_rows()

# ---------- Save final failed ----------
if failed:
    with open(FAILED_TXT, "a", encoding="utf-8") as f:
        for line in failed:
            f.write(line + "\n")

# ---------- Final summary ----------
total_time = time.time() - start_time
total_samples = stats['success'] + stats['existed']
avg_duration = stats['total_duration'] / max(total_samples, 1)
total_hours = stats['total_duration'] / 3600

print(f"\n{'='*60}")
print("🎉 DATASET GENERATION COMPLETED")
print(f"{'='*60}")
print(f"✅ Newly Generated: {stats['success']:,} files")
print(f"⊙ Already Existed:  {stats['existed']:,} files")
print(f"❌ Failed:          {stats['failed']:,} files")
print(f"{'─'*60}")
print(f"📊 Total Valid:     {total_samples:,} samples")
print(f"💾 CSV Records:     {len(train_df):,} rows")
print(f"⏱️  Total Time:      {timedelta(seconds=int(total_time))}")

if total_time > 0 and stats['actual_processed'] > 0:
    avg_speed = stats['actual_processed'] / total_time
    print(f"⚡ Avg Speed:       {avg_speed:.2f} files/s")

print(f"🎵 Avg Duration:    {avg_duration:.2f}s per audio")
print(f"💿 Total Audio:     {total_hours:.2f} hours")
print(f"{'='*60}\n")

# Additional stats
if stats['actual_processed'] > 0:
    success_rate = stats['success'] / stats['actual_processed'] * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
if stats['failed'] > 0:
    print(f"⚠️  Check '{FAILED_TXT}' for {stats['failed']} failed files")

if os.path.exists(BACKUP_DIR):
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("train_backup")]
    if backups:
        print(f"💾 {len(backups)} backup(s) saved in '{BACKUP_DIR}'")

print(f"\n📁 Dataset location: {OUTPUT_DIR}")
print(f"   ├── clips/           ({total_samples:,} wav files)")
print(f"   ├── train.csv        ({len(train_df):,} rows)")
print(f"   ├── backups/         ({len(backups) if backups else 0} checkpoints)")
print(f"   └── failed.txt       ({stats['failed']} failed)")