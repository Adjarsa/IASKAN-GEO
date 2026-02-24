import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));

// Note: React.StrictMode désactivé temporairement à cause d'un conflit connu
// entre React 19 et les composants Radix UI Portal (DropdownMenu, Dialog, etc.)
// qui cause l'erreur "insertBefore" lors du double-rendu de StrictMode.
// Réactiver quand Radix UI v2+ résoudra ce problème de compatibilité.
root.render(<App />);
