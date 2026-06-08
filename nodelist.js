function initQueue() {
  return {
    collection: []
  };
}

function enqueue(queue, element) {
  queue.collection.push(element);   // thêm vào cuối
}

function dequeue(queue) {
  return queue.collection.shift();   // xóa và trả về phần tử đầu
}

function front(queue) {
  if (queue.collection.length === 0) return undefined;
  return queue.collection[0];        // xem phần tử đầu, không xóa
}

function size(queue) {
  return queue.collection.length;    // trả về số lượng
}

function isEmpty(queue) {
  return queue.collection.length === 0;  // kiểm tra rỗng
}
