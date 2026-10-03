import { NavLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";

const workspaceLinks = [
  ["dashboard", "Vue d’ensemble", "⌂"],
  ["reviews", "Avis", "◌"],
  ["cases", "Dossiers", "◇"],
  ["analysis", "Analyse", "↗"],
  ["notifications", "Notifications", "◍"],
  ["billing", "Facturation", "€"],
] as const;

function getLinkClass(isActive: boolean) {
  return isActive ? "side-link active" : "side-link";
}

export function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const canAccessAdmin = ["OWNER", "ADMIN", "admin", "owner"].includes(
    user?.role ?? "",
  );

  const accountInitial = (user?.email?.[0] ?? "U").toUpperCase();
  const currentPath = location.pathname.replace("/app", "") || "/";

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink to="/app/dashboard" className="brand">
          <span className="brand-mark">R</span>
          <span>review defense</span>
        </NavLink>

        <div className="sidebar-section">
          <span className="sidebar-label">Espace de travail</span>

          {workspaceLinks.map(([id, label, icon]) => (
            <NavLink
              key={id}
              to={`/app/${id}`}
              className={({ isActive }) => getLinkClass(isActive)}
            >
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </div>

        <div className="sidebar-bottom">
          {canAccessAdmin && (
            <NavLink
              to="/app/admin"
              className={({ isActive }) => getLinkClass(isActive)}
            >
              <span>✦</span>
              Administration
            </NavLink>
          )}

          <NavLink
            to="/app/settings"
            className={({ isActive }) => getLinkClass(isActive)}
          >
            <span>⚙</span>
            Paramètres
          </NavLink>

          <div className="account-chip">
            <div className="avatar">{accountInitial}</div>

            <div>
              <strong>{user?.email ?? "Compte"}</strong>
              <small>{user?.role ?? "Utilisateur"}</small>
            </div>

            <button
              type="button"
              onClick={() => void logout()}
              aria-label="Se déconnecter"
            >
              ↗
            </button>
          </div>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-topbar">
          <div>
            <span className="topbar-context">Espace client</span>
            <span className="topbar-path">{currentPath}</span>
          </div>

          <div className="topbar-actions">
            <span className="live-dot">● Connecté</span>
            <button
              type="button"
              className="icon-button"
              onClick={() => void logout()}
              aria-label="Déconnexion"
            >
              ↗
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
