giải thích luồng hoạt động cho ta
const { useState } = React;

export const ColorPicker = () => {
 const [color, setColor] = useState("#ffffff");

return (
  <div id="color-picker-container" style={{ backgroundColor: color }}>
  <input
   type="color" 
   id="color-input" 
   onChange={(e) => setColor(e.target.value)}
   value={color}
  />
  </div>
)
};

<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8" />
    <title>Color Picker</title>
    <link rel="stylesheet" href="styles.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.development.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.development.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.26.5/babel.min.js"></script>
    <script
      data-plugins="transform-modules-umd"
      type="text/babel"
      src="index.jsx"
    ></script>
</head>

<body>
    <div id="root"></div>
    <script
      data-plugins="transform-modules-umd"
      type="text/babel"
      data-presets="react"
      data-type="module"
    >
      import { ColorPicker } from './index.jsx';
      ReactDOM.createRoot(document.getElementById('root')).render(<ColorPicker />);
    </script>
</body>

</html>
body,
html {
    margin: 0;
    padding: 0;
    height: 100%;
    font-family: Arial, sans-serif;
}

#color-picker-container {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    background-color: #ffffff;
}

input[type="color"] {
    position: absolute;
    margin-top: 50px;
    height: 40px;
}
