// Administration de l'organisation : liste les membres et gère les invitations via l'API /v1.
// Les contrôles de rôle affichés dans l'écran servent à guider l'interface ; les opérations
// de lecture, d'invitation et de changement de rôle doivent être autorisées à nouveau côté serveur.
// AuthContext fournit le rôle courant, tandis que les données membres restent chargées depuis l'API.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { FeedbackMessage } from "@/components/layout/FeedbackMessage";
import { PageHeading } from "@/components/layout/PageHeading";
import { api } from "@/services/api/client";

type OrganizationMember = {
  user_id: string;
  email: string;
  role: string;
};

type Invitation = {
  invitation_id: string;
  email: string;
  role: string;
  expires_at?: string;
};

/**
 * Organization administration screen.
 *
 * Members and invitations are managed through organization-scoped API routes.
 * The backend remains the authority for role and permission checks.
 */
export function AdminPage() {
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [lastInvitation, setLastInvitation] = useState<Invitation | null>(null);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("ANALYST");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isOwner = user?.role === "OWNER";

  async function loadMembers() {
    try {
      const response = await api.get<{ items: OrganizationMember[] }>(
        "/v1/organization/members",
      );
      setMembers(response.items ?? []);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Administration indisponible",
      );
    }
  }

  useEffect(() => {
    void loadMembers();
  }, []);

  async function inviteMember() {
    setError("");
    setBusy(true);

    try {
      const response = await api.post<Invitation>(
        "/v1/organization/invitations",
        { email, role },
      );

      setLastInvitation({
        invitation_id: response.invitation_id,
        email: response.email ?? email,
        role: response.role ?? role,
        expires_at: response.expires_at,
      });
      setEmail("");
      await loadMembers();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Invitation impossible",
      );
    } finally {
      setBusy(false);
    }
  }

  async function changeMemberRole(userId: string, nextRole: string) {
    setError("");

    try {
      await api.post(`/v1/organization/members/${userId}/role`, {
        role: nextRole,
      });
      await loadMembers();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Modification impossible",
      );
    }
  }

  async function revokeSessions() {
    setError("");
    setBusy(true);

    try {
      await api.post("/v1/auth/revoke-all");
      await logout().catch(() => undefined);
      navigate("/login", { replace: true });
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : "Révocation impossible",
      );
      setBusy(false);
    }
  }

  return (
    <section className="workspace">
      <PageHeading
        eyebrow="ADMINISTRATION"
        title="L’espace de contrôle."
        description="Membres, rôles, invitations et sessions de l’organisation."
        action={
          <button
            className="button button-dark"
            disabled={busy}
            onClick={() => void revokeSessions()}
          >
            Révoquer mes sessions et me déconnecter
          </button>
        }
      />

      {error && (
        <FeedbackMessage className="form-error" role="alert">
          {error}
        </FeedbackMessage>
      )}

      <div className="create-bar">
        <input
          type="email"
          placeholder="adresse@entreprise.fr"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <select value={role} onChange={(event) => setRole(event.target.value)}>
          <option>ANALYST</option>
          <option>CLIENT</option>
          <option>VIEWER</option>
          <option>ADMIN</option>
        </select>

        <button
          className="button button-secondary"
          disabled={busy || !email.trim()}
          onClick={() => void inviteMember()}
        >
          Inviter →
        </button>
      </div>

      {lastInvitation && (
        <article className="panel">
          <span className="eyebrow">DERNIÈRE INVITATION CRÉÉE</span>
          <h2>{lastInvitation.email}</h2>
          <p>
            {lastInvitation.role} · expiration{" "}
            {lastInvitation.expires_at ?? "non communiquée"}
          </p>
          <small>
            La route API actuelle permet de créer une invitation, mais ne
            fournit pas de consultation de la liste des invitations existantes.
          </small>
        </article>
      )}

      <div className="panel table-panel">
        {members.map((member) => (
          <div className="case-row" key={member.user_id}>
            <div className="avatar">
              {(member.email?.[0] ?? "U").toUpperCase()}
            </div>

            <div>
              <b>{member.email}</b>
              <p>{member.user_id}</p>
            </div>

            <select
              value={member.role}
              onChange={(event) =>
                void changeMemberRole(member.user_id, event.target.value)
              }
            >
              {(isOwner || member.role === "OWNER") && <option>OWNER</option>}
              <option>ADMIN</option>
              <option>ANALYST</option>
              <option>CLIENT</option>
              <option>VIEWER</option>
            </select>

            <span>↗</span>
          </div>
        ))}
      </div>
    </section>
  );
}
