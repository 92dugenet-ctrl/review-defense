import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { HomePage } from "@/pages/HomePage";
import { NotFoundPage } from "@/pages/NotFoundPage";

const Placeholder = ({ title }: { title: string }) => (
  <section className="page-placeholder">
    <span className="eyebrow">REVIEW DEFENSE · SOCLE</span>
    <h1>{title}</h1>
    <p>Cette surface est réservée au prochain chantier fonctionnel.</p>
  </section>
);

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/app",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/app/dashboard" replace /> },
      { path: "dashboard", element: <Placeholder title="Tableau de bord" /> },
      { path: "reviews", element: <Placeholder title="Avis" /> },
      { path: "cases", element: <Placeholder title="Dossiers" /> },
      { path: "analysis", element: <Placeholder title="Analyse" /> },
      { path: "notifications", element: <Placeholder title="Notifications" /> },
      { path: "billing", element: <Placeholder title="Facturation" /> },
      { path: "settings", element: <Placeholder title="Paramètres" /> },
      { path: "admin", element: <Placeholder title="Administration" /> }
    ],
  },
  { path: "/login", element: <Placeholder title="Connexion" /> },
  { path: "/register", element: <Placeholder title="Créer un compte" /> },
  { path: "*", element: <NotFoundPage /> },
]);