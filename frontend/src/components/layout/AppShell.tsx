import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

type IconName = "dashboard" | "reviews" | "cases" | "analysis" | "notifications" | "billing" | "settings" | "admin";

type NavigationItem = {
  path: string;
  label: string;
  icon: IconName;
};

const navigation: NavigationItem[] = [
  { path: "dashboard", label: "Tableau de bord", icon: "dashboard" },
  { path: "reviews", label: "Avis", icon: "reviews" },
  { path: "cases", label: "Dossiers", icon: "cases" },
  { path: "analysis", label: "Analyse", icon: "analysis" },
  { path: "notifications", label: "Notifications", icon: "notifications" },
];

const workspaceNavigation: NavigationItem[] = [
  { path: "billing", label: "Facturation", icon: "billing" },
  { path: "settings", label: "Paramètres", icon: "settings" },
];

function Icon({ name }: { name: IconName }) {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true };
  const paths: Record<IconName, React.ReactNode> = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    reviews: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H8l-4 2v-4.2A7.5 7.5 0 1 1 20 11.5Z" /><path d="m8.5 11.5 2 2 5-5" /></>,
    cases: <><path d="M4 7.5h16v12H4z" /><path d="M8 7.5V5h8v2.5M9 12h6" /></>,
    analysis: <><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /><path d="m4 7 6-3 6 4 6-5" /></>,
    notifications: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4" /></>,
    billing: <><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 10h18M7 15h4" /></>,
    settings: <><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z" /><path d="m19.4 15 .1.1a2 2 0 0 1-2.8 2.8l-.1-.1a2 2 0 0 0-3.4 1.4v.2a2 2 0 0 1-4 0v-.2a2 2 0 0 0-3.4-1.4l-.1.1A2 2 0 0 1 3 15.1l.1-.1a2 2 0 0 0-1.4-3.4h-.2a2 2 0 0 1 0-4h.2A2 2 0 0 0 3.1 4.2L3 4.1a2 2 0 0 1 2.8-2.8l.1.1A2 2 0 0 0 9.3 0h.2a2 2 0 0 1 4 0v.2a2 2 0 0 0 3.4 1.4l.1-.1A2 2 0 0 1 19.8 4l-.1.1a2 2 0 0 0 1.4 3.4h.2a2 2 0 0 1 0 4h-.2a2 2 0 0 0-1.7 3.5Z" /></>,
    admin: <><path d="M12 3 4 6v5c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-3Z" /><path d="m9 12 2 2 4-4" /></>,
  };

  return <svg {...common}>{paths[name]}</svg>;
}

const pageTitles: Record<string, string> = {
  "/app/dashboard": "Tableau de bord",
  "/app/reviews": "Avis",
  "/app/cases": "Dossiers",
  "/app/analysis": "Analyse",
  "/app/notifications": "Notifications",
  "/app/billing": "Facturation",
  "/app/settings": "Paramètres",
  "/app/admin": "Administration",
};

function NavItem({ item, onNavigate }: { item: NavigationItem; onNavigate: () => void }) {
  return (
    <NavLink
      to={`/app/${item.path}`}
      onClick={onNavigate}
      className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}
    >
      <Icon name={item.icon} />
      <span>{item.label}</span>
    </NavLink>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  async function signOut() {
    await logout();
    navigate("/login", { replace: true });
  }

  const initials = user?.email.slice(0, 2).toUpperCase() ?? "RD";
  const isAdmin = user?.role === "ADMIN" || user?.role === "OWNER" || user?.role === "admin" || user?.role === "owner";
  const pageTitle = pageTitles[location.pathname] ?? "Workspace";
  const closeMobile = () => setMobileOpen(false);

  return (
    <div className="app-shell">
      {mobileOpen && <button className="sidebar-backdrop" aria-label="Fermer le menu" onClick={closeMobile} />}
      <aside className={mobileOpen ? "sidebar mobile-open" : "sidebar"}>
        <div className="brand">
          <span className="brand-mark">RD</span>
          <span className="brand-copy"><strong>Review Defense</strong><small>Workspace</small></span>
          <button className="mobile-close" aria-label="Fermer le menu" onClick={closeMobile}>×</button>
        </div>

        <div className="workspace-switcher">
          <span className="workspace-avatar">{initials}</span>
          <span><small>Organisation</small><strong>{user?.organization_id ?? "Workspace"}</strong></span>
        </div>

        <nav className="sidebar-nav" aria-label="Navigation principale">
          <span className="nav-section-label">Espace de travail</span>
          {navigation.map((item) => <NavItem key={item.path} item={item} onNavigate={closeMobile} />)}

          <span className="nav-section-label nav-section-secondary">Configuration</span>
          {workspaceNavigation.map((item) => <NavItem key={item.path} item={item} onNavigate={closeMobile} />)}
          {isAdmin && <NavItem item={{ path: "admin", label: "Administration", icon: "admin" }} onNavigate={closeMobile} />}
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot" />
          <span>Session sécurisée</span>
        </div>
      </aside>

      <div className="app-content">
        <header className="topbar">
          <button className="mobile-menu" aria-label="Ouvrir le menu" onClick={() => setMobileOpen(true)}>☰</button>
          <div className="topbar-title">
            <span className="topbar-kicker">REVIEW DEFENSE · WORKSPACE</span>
            <h1>{pageTitle}</h1>
          </div>
          <div className="topbar-actions">
            <div className="topbar-user">
              <div className="avatar" aria-hidden="true">{initials}</div>
              <div><strong>{user?.email ?? "Utilisateur"}</strong><span>{user?.role ?? "member"}</span></div>
            </div>
            <button className="button button-secondary topbar-logout" onClick={signOut}>Déconnexion</button>
          </div>
        </header>

        <main className="page-content"><Outlet /></main>
      </div>
    </div>
  );
}
