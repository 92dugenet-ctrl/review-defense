import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

const navigation = [
  ["dashboard", "Tableau de bord"],
  ["reviews", "Avis"],
  ["cases", "Dossiers"],
  ["analysis", "Analyse"],
  ["notifications", "Notifications"],
  ["billing", "Facturation"],
  ["settings", "Paramètres"],
] as const;

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function signOut() {
    await logout();
    navigate("/login", { replace: true });
  }

  const initials = user?.email.slice(0, 2).toUpperCase() ?? "RD";

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">RD</span>
          <span><strong>Review Defense</strong><small>Workspace</small></span>
        </div>
        <nav className="sidebar-nav" aria-label="Navigation application">
          {navigation.map(([path, label]) => (
            <NavLink key={path} to={`/app/${path}`} className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>{label}</NavLink>
          ))}
        </nav>
        <div className="sidebar-footer"><span className="status-dot" /><span>Session sécurisée</span></div>
      </aside>
      <div className="app-content">
        <header className="topbar">
          <div><span className="topbar-kicker">ORGANISATION</span><strong>{user?.organization_id ?? "Workspace"}</strong></div>
          <div className="topbar-actions">
            <div className="avatar" aria-label={user?.email ?? "Profil"}>{initials}</div>
            <button className="button button-secondary topbar-logout" onClick={signOut}>Déconnexion</button>
          </div>
        </header>
        <main className="page-content"><Outlet /></main>
      </div>
    </div>
  );
}
