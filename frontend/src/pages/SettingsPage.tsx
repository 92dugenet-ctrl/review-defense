// Paramètres du compte connecté : assemble les informations issues d'AuthContext et les liens
// vers les fonctions de confidentialité et de gestion de session. Cette page n'est pas un dépôt
// autonome de profil : les changements sensibles sont réalisés par les écrans/API spécialisés.

import { Link } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { DetailMeta } from "@/components/layout/DetailMeta";
import { PageHeading } from "@/components/layout/PageHeading";

/** Shows account details, privacy settings entry point and session controls. */
export function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <section className="workspace">
      <PageHeading
        eyebrow="PARAMÈTRES"
        title="Votre espace."
        description="Identité, confidentialité et session au même endroit."
      />

      <div className="content-grid">
        <article className="panel">
          <span className="eyebrow">COMPTE</span>
          <h2>Informations</h2>

          <DetailMeta>
            <span>E-mail</span>
            <b>{user?.email ?? "—"}</b>

            <span>Organisation</span>
            <b>{user?.organization_id ?? "—"}</b>

            <span>Rôle</span>
            <b>{user?.role ?? "—"}</b>
          </DetailMeta>
        </article>

        <article className="panel">
          <span className="eyebrow">DONNÉES</span>
          <h2>Confidentialité</h2>
          <p>
            Gérez vos demandes d’accès, de rectification, d’effacement et de
            portabilité.
          </p>
          <Link className="button button-secondary" to="/app/privacy">
            Gérer mes données →
          </Link>
        </article>
      </div>

      <article className="panel">
        <span className="eyebrow">SESSION</span>
        <h2>Terminer la session</h2>
        <p>Déconnectez ce navigateur de votre espace.</p>
        <button
          className="button button-ghost"
          onClick={() => void logout()}
        >
          Se déconnecter
        </button>
      </article>
    </section>
  );
}
