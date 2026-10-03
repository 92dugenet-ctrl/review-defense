import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import "@/styles/muse-v3.css";

/**
 * Sign-in screen for existing Review Defense workspaces.
 *
 * The authentication provider owns the API request and session persistence.
 * This page only collects credentials, displays errors and redirects on success.
 */
export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organizationId, setOrganizationId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password, organizationId);
      navigate("/app/dashboard");
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Connexion impossible",
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
          <div className="muse-eyebrow">ESPACE CLIENT</div>
          <h1>
            Bon retour.
            <br />
            <em>Le dossier continue.</em>
          </h1>
          <p>
            Retrouvez vos dossiers, vos preuves et les validations en attente
            là où vous les avez laissés.
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
              Organisation ID
              <input
                value={organizationId}
                onChange={(event) => setOrganizationId(event.target.value)}
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
                required
                autoComplete="current-password"
              />
            </label>

            <button className="muse-pill muse-blue" disabled={loading}>
              {loading ? "Connexion…" : "Se connecter →"}
            </button>
          </form>

          <p>
            Pas encore de compte ? <Link to="/register">Créer un espace</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
