// Garde de navigation côté client : attend la restauration de session puis redirige les visiteurs non authentifiés vers la connexion. Cette protection masque les pages dans l'interface, mais n'est pas une autorisation : chaque endpoint doit refaire ses propres contrôles.

import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export function RequireAuth() {
  const { loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return <main className="center-page"><strong>Vérification de la session…</strong></main>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
