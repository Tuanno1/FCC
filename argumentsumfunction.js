function addTogether(a, b) {
  // Hàm kiểm tra số
  function isNumber(value) {
    return typeof value === "number" && !isNaN(value);
  }
  
  // Trường hợp 1: CHỈ CÓ 1 THAM SỐ (arguments.length === 1)
  if (arguments.length === 1) {
    // Nếu tham số không phải số → undefined
    if (!isNumber(a)) {
      return undefined;
    }
    // Currying: trả về hàm mới
    return function(c) {
      // Kiểm tra tham số c
      if (!isNumber(c)) {
        return undefined;
      }
      return a + c;
    };
  }
  
  // Trường hợp 2: CÓ 2 THAM SỐ (arguments.length === 2)
  // Kiểm tra cả hai đều là số
  if (!isNumber(a) || !isNumber(b)) {
    return undefined;
  }
  
  // Cộng hai số
  return a + b;
}
