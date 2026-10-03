/**
 * Point d'entrée React de la nouvelle interface applicative.
 *
 * Vite charge ce module depuis react.html. Il monte l'arbre React dans
 * l'élément DOM #root, charge les styles globaux, puis installe les
 * fournisseurs d'authentification et de navigation autour des pages.
 *
 * À distinguer de frontend/index.html et du workspace historique servi
 * directement par wsgi.py : les deux parcours coexistent pendant la migration.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "@/auth/AuthContext";
import { router } from "@/app/router";
import "@/styles/tokens.css";
import "@/styles/global.css";

// createRoot connecte React au nœud HTML prévu par react.html.
// Le non-null (!) exprime ici le contrat : ce point d'entrée doit fournir #root.
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* AuthProvider rend l'état de session accessible aux pages et routes. */}
    <AuthProvider>
      {/* RouterProvider choisit l'écran à afficher selon l'URL courante. */}
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
);
