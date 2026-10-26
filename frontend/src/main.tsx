import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/global.css";
import { applyTheme, getStoredTheme } from "./lib/theme";

// Apply the persisted theme before React paints, so there is no flash.
applyTheme(getStoredTheme());

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
