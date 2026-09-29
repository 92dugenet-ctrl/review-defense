import { useAuth } from "@/auth/AuthContext";

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <section className="page-placeholder">
      <span className="eyebrow">REVIEW DEFENSE · WORKSPACE</span>
      <h1>Tableau de bord</h1>
      <p>Session active pour <strong>{user?.email}</strong>. Le workspace est maintenant protégé par l’authentification du backend.</p>
      <div className="auth-session-grid">
        <div><small>RÔLE</small><strong>{user?.role}</strong></div>
        <div><small>ORGANISATION</small><strong>{user?.organization_id}</strong></div>
        <div><small>IDENTITÉ</small><strong>{user?.user_id}</strong></div>
      </div>
    </section>
  );
}
