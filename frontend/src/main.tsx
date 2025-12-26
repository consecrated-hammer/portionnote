import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/index.css";

const RootElement = document.getElementById("root");

if (!RootElement) {
  throw new Error("Root element not found");
}

const Root = createRoot(RootElement);

Root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
