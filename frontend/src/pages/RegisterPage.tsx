import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import "@/styles/muse-v3.css";

/**
 * Registration screen for a new Review Defense workspace.
 *
 * Account creation and session handling are delegated to AuthContext so that
 * registration follows the same session rules as sign-in.
 */
export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register(email, organizationName, password);
      navigate("/app/dashboard");
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Inscription impossible",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="muse-auth">
      <Link className="muse-brand muse-auth-brand" to="/">
        ◉ <span>Review Defense</span>
      </Link>

      <div className="muse-auth-grid">
        <div className="muse-auth-copy">
          <div className="muse-eyebrow">NOUVEL ESPACE</div>
          <h1>
            Commencez ici.
            <br />
            <em>Structurez le travail.</em>
          </h1>
          <p>
            Créez votre espace de travail et commencez avec les dossiers qui
            demandent déjà votre attention.
          </p>
        </div>

        <div className="muse-auth-card">
          {error && <div className="muse-auth-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <label>
              E-mail
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />
            </label>

            <label>
              Nom de l’organisation
              <input
                value={organizationName}
                onChange={(event) => setOrganizationName(event.target.value)}
                required
                autoComplete="organization"
              />
            </label>

            <label>
              Mot de passe
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={12}
                required
                autoComplete="new-password"
              />
              <small>12 caractères minimum.</small>
            </label>

            <button className="muse-pill muse-blue" disabled={loading}>
              {loading ? "Création…" : "Créer mon espace →"}
            </button>
          </form>

          <p>
            Déjà un compte ? <Link to="/login">Se connecter</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
