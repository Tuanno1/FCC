
export function Footer() {
  return (
    <footer className="footer">

      <div className="footer-links">

        <ul>
          <li><a href="#">Bless</a></li>
          <li><a href="#">Faith</a></li>
        </ul>

        <ul>
          <li><a href="#">Gracious</a></li>
          <li><a href="#">Mercy</a></li>
        </ul>

        <ul>
          <li><a href="#">Hallelujah</a></li>
          <li><a href="#">Praise</a></li>
        </ul>

      </div>

      <p className="copyright">
        © 2026 Kingdom Project. All Rights Reserved.
      </p>

      <div className="socials">
        <a href="#">✝️</a>
        <a href="#">📖</a>
        <a href="#">🙏</a>
      </div>

    </footer>
  );
}
/* RESET */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* BODY */

body {
  min-height: 100vh;

  display: flex;
  justify-content: center;
  align-items: center;

  background: #f4f4f7;

  font-family:
    Inter,
    -apple-system,
    BlinkMacSystemFont,
    sans-serif;

  padding: 30px;
}

/* FOOTER CARD */

.footer {

  width: min(950px, 90vw);

  background: #e5e3eb;

  border-radius: 28px;

  padding: 60px 70px;

  box-shadow:
    0 12px 40px rgba(0,0,0,0.08);
}

/* 3 CỘT */

.footer-links {

  display: grid;

  grid-template-columns:
    repeat(3, 1fr);

  gap: 60px;

  margin-bottom: 50px;
}

/* DANH SÁCH */

.footer-links ul {
  list-style: none;
}

.footer-links li {
  margin-bottom: 14px;
}

/* LINK */

.footer-links a {

  text-decoration: none;

  color: #222;

  font-size: 18px;

  font-weight: 500;

  transition: .25s;
}

.footer-links a:hover {

  color: #444;

  opacity: .75;
}

/* COPYRIGHT */

.copyright {

  text-align: center;

  color: #666;

  font-size: 14px;

  margin-bottom: 30px;
}

/* ICONS */

.socials {

  display: flex;

  justify-content: center;

  gap: 20px;
}

.socials a {

  width: 44px;

  height: 44px;

  display: flex;

  justify-content: center;

  align-items: center;

  text-decoration: none;

  border-radius: 50%;

  background: rgba(255,255,255,.5);

  font-size: 20px;

  transition: .25s;
}

.socials a:hover {

  transform: translateY(-3px);

  background: white;
}

<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Reusable Footer Component</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.development.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.development.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.26.3/babel.min.js"></script>
    <script
      data-plugins="transform-modules-umd"
      type="text/babel"
      src="index.jsx"
    ></script>
    <link rel="stylesheet" href="styles.css" />
  </head>

  <body>
    <div id="root"></div>
    <script
      data-plugins="transform-modules-umd"
      type="text/babel"
      data-presets="react"
      data-type="module"
    >
      import { Footer } from './index.jsx';
      ReactDOM.createRoot(document.getElementById('root')).render(<Footer />);
    </script>
  </body>
</html>
