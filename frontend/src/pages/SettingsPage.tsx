import { Link } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export function SettingsPage() {
  const { user, logout } = useAuth();
  return <section className="module-page">
    <div className="module-heading"><div><span className="eyebrow">REVIEW DEFENSE · COMPTE</span><h1>Paramètres</h1><p>Informations du compte et accès aux réglages de confidentialité.</p></div></div>
    <div className="dashboard-main-grid">
      <article className="dashboard-card"><span className="dashboard-card-kicker">COMPTE</span><h2>Informations du compte</h2>
        <div className="workspace-row"><strong>E-mail</strong><span>{user?.email ?? "—"}</span></div>
        <div className="workspace-row"><strong>Organisation</strong><span>{user?.organization_id ?? "—"}</span></div>
        <div className="workspace-row"><strong>Rôle</strong><span>{user?.role ?? "—"}</span></div>
      </article>
      <article className="dashboard-card"><span className="dashboard-card-kicker">DONNÉES</span><h2>Confidentialité & RGPD</h2><p>Exportez vos données et suivez vos demandes.</p><Link className="button button-secondary" to="/app/privacy">Gérer mes données</Link></article>
    </div>
    <article className="dashboard-card"><span className="dashboard-card-kicker">SESSION</span><h2>Session actuelle</h2><p>Déconnectez cette session depuis cet espace.</p><button className="button button-ghost" type="button" onClick={() => void logout()}>Se déconnecter</button></article>
  </section>;
}
