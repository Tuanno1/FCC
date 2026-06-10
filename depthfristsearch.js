function dfs(graph, root) {
  const stack = [root];
  const visited = [];
  const n = graph.length;
  
  while (stack.length > 0) {
    const current = stack.pop();
    
    if (!visited.includes(current)) {
      visited.push(current);
      
      for (let neighbor = n - 1; neighbor >= 0; neighbor--) {
        if (graph[current][neighbor] === 1 && !visited.includes(neighbor)) {
          stack.push(neighbor);
        }
      }
    }
  }
  
  return visited;
}
