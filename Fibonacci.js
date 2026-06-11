function fibonacci(n) {
  // Test 3: Khởi tạo mảng sequence với [0, 1]
  const sequence = [0, 1];
  
  // Nếu n <= 1, trả về giá trị tương ứng trong sequence
  if (n <= 1) {
    return sequence[n];
  }
  
  // Dùng vòng lặp để tính các số Fibonacci từ 2 đến n
  // KHÔNG dùng đệ quy!
  for (let i = 2; i <= n; i++) {
    // Mỗi số Fibonacci mới = tổng 2 số trước đó
    const nextFib = sequence[i - 1] + sequence[i - 2];
    sequence.push(nextFib);
  }
  
  // Trả về số thứ n
  return sequence[n];
}
