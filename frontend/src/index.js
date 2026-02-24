import React from "react";
import ReactDOM from "react-dom/client";
import * as Portal from "@radix-ui/react-portal";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));

// Portal.Provider résout le conflit entre React 19 et les composants Radix UI Portal
// qui causait l'erreur "insertBefore" lors du rendu
root.render(
  <Portal.Root>
    <App />
  </Portal.Root>
);
