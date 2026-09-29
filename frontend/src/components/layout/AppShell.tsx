import { NavLink, Outlet } from "react-router-dom";

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
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">RD</span>
          <span>
            <strong>Review Defense</strong>
            <small>Workspace</small>
          </span>
        </div>

        <nav className="sidebar-nav" aria-label="Navigation application">
          {navigation.map(([path, label]) => (
            <NavLink
              key={path}
              to={`/app/${path}`}
              className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Service opérationnel</span>
        </div>
      </aside>

      <div className="app-content">
        <header className="topbar">
          <div>
            <span className="topbar-kicker">ORGANISATION</span>
            <strong>Workspace</strong>
          </div>
          <div className="topbar-actions">
            <button className="icon-button" aria-label="Notifications">●</button>
            <div className="avatar" aria-label="Profil">GD</div>
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}