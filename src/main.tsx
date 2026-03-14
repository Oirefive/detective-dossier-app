import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/app.css";

document.title = "Архив расследований";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
