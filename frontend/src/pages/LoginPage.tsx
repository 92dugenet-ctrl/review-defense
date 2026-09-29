import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "@/services/api/client";
import { useAuth } from "@/auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [organizationId, setOrganizationId] = useState(sessionStorage.getItem("review-defense.organization-id") ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email.trim(), password, organizationId.trim());
      const destination = (location.state as { from?: string } | null)?.from ?? "/app/dashboard";
      navigate(destination, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Connexion impossible.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="auth-brand" to="/">Review Defense</Link>
        <span className="eyebrow">ESPACE SÉCURISÉ</span>
        <h1>Connexion</h1>
        <p className="auth-intro">Accédez à votre workspace et à vos dossiers.</p>
        <form onSubmit={submit} className="auth-form">
          <label>E-mail<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label>Identifiant organisation<input value={organizationId} onChange={(e) => setOrganizationId(e.target.value)} placeholder="UUID de votre organisation" required /></label>
          <label>Mot de passe<input type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary auth-submit" disabled={submitting}>{submitting ? "Connexion…" : "Se connecter"}</button>
        </form>
        <p className="auth-switch">Pas encore de compte ? <Link to="/register">Créer un compte</Link></p>
      </section>
    </main>
  );
}
