import React from "react";
import ReactDOM from "react-dom/client";

// Styling order matters (01_architecture.md §1.4): theme → primereact → icons →
// primeflex → bootstrap → project overrides (last wins).
import "primereact/resources/themes/lara-light-blue/theme.css";
import "primereact/resources/primereact.min.css";
import "primeicons/primeicons.css";
import "primeflex/primeflex.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles/app.css";

import App from "./App.jsx";
import "./i18n/config.js";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
