import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "@/services/api/client";
import { useAuth } from "@/auth/AuthContext";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [organizationName, setOrganizationName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (password !== confirmation) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    setSubmitting(true);
    try {
      await register(email.trim(), organizationName.trim(), password);
      navigate("/app/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Création du compte impossible.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link className="auth-brand" to="/">Review Defense</Link>
        <span className="eyebrow">NOUVEAU WORKSPACE</span>
        <h1>Créer un compte</h1>
        <p className="auth-intro">Créez votre organisation et son premier compte administrateur.</p>
        <form onSubmit={submit} className="auth-form">
          <label>Organisation<input value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} required maxLength={200} /></label>
          <label>E-mail<input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label>Mot de passe<input type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={12} required /><small>12 caractères minimum.</small></label>
          <label>Confirmation<input type="password" autoComplete="new-password" value={confirmation} onChange={(e) => setConfirmation(e.target.value)} required /></label>
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary auth-submit" disabled={submitting}>{submitting ? "Création…" : "Créer le workspace"}</button>
        </form>
        <p className="auth-switch">Déjà un compte ? <Link to="/login">Se connecter</Link></p>
      </section>
    </main>
  );
}
