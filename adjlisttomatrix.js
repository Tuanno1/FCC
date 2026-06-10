function adjacencyListToMatrix(adjList) {
  const nodes = Object.keys(adjList);  // ["0", "1", "2", "3"]
  const n = nodes.length;              // 4
  
  const matrix = Array.from({ length: n }, () => Array(n).fill(0));
  
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    const neighbors = adjList[node];
    
    for (let neighbor of neighbors) {
      const neighborIndex = nodes.indexOf(String(neighbor));
      matrix[i][neighborIndex] = 1;
    }
     for (let row of matrix) {
    console.log(row);
  }
  }
  
  return matrix;
}
