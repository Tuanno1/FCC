function dfsNQueens(n) {
  if (n < 1) return [];
  if (n === 1) return [[0]];
  if (n === 2 || n === 3) return [];
  
  const result = [];
  const board = [];
  
  function isSafe(row, col) {
    for (let prevRow = 0; prevRow < row; prevRow++) {
      const prevCol = board[prevRow];
      if (prevCol === col) return false;
      if (Math.abs(prevCol - col) === Math.abs(prevRow - row)) return false;
    }
    return true;
  }
  
  function dfs(row) {
    if (row === n) {
      result.push([...board]);
      return;
    }
    
    for (let col = 0; col < n; col++) {
      if (isSafe(row, col)) {
        board[row] = col;
        dfs(row + 1);
      }
    }
  }
  
  dfs(0);
  return result;
}
