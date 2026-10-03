import { useEffect, useState } from "react";
import { api } from "@/services/api/client";

export function AdminPage() {
  const [members, setMembers] = useState<any[]>([]);
  const [invites, setInvites] = useState<any[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("ANALYST");
  const [error, setError] = useState("");

  const load = () =>
    Promise.all([
      api.get<any>("/v1/organization/members"),
      api.get<any>("/v1/organization/invitations"),
    ])
      .then(([membersResponse, invitationsResponse]) => {
        setMembers(membersResponse.items ?? []);
        setInvites(invitationsResponse.items ?? []);
      })
      .catch((requestError) => {
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Administration indisponible",
        );
      });

  useEffect(() => {
    void load();
  }, []);

  const invite = async () => {
    try {
      await api.post("/v1/organization/invitations", {
        email,
        role,
      });
      setEmail("");
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Invitation impossible",
      );
    }
  };

  const change = async (userId: string, nextRole: string) => {
    try {
      await api.patch(
        "/v1/organization/members/" + userId + "/role",
        { role: nextRole },
      );
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Modification impossible",
      );
    }
  };

  const revokeSessions = async () => {
    try {
      await api.post("/v1/auth/revoke-all");
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Révocation impossible",
      );
    }
  };

  return (
    <section className="workspace">
      <div className="page-title">
        <div>
          <span className="eyebrow">ADMINISTRATION</span>
          <h1>L’espace de contrôle.</h1>
          <p>Membres, rôles, invitations et sessions de l’organisation.</p>
        </div>
        <button
          className="button button-dark"
          onClick={revokeSessions}
        >
          Révoquer les sessions
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="create-bar">
        <input
          placeholder="adresse@entreprise.fr"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <select
          value={role}
          onChange={(event) => setRole(event.target.value)}
        >
          <option>ANALYST</option>
          <option>CLIENT</option>
          <option>VIEWER</option>
          <option>ADMIN</option>
        </select>
        <button
          className="button button-secondary"
          onClick={() => void invite()}
        >
          Inviter →
        </button>
      </div>

      <div className="panel table-panel">
        {members.map((member) => (
          <div
            className="case-row"
            key={member.user_id}
          >
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
                void change(member.user_id, event.target.value)
              }
            >
              <option>OWNER</option>
              <option>ADMIN</option>
              <option>ANALYST</option>
              <option>CLIENT</option>
              <option>VIEWER</option>
            </select>
            <span>↗</span>
          </div>
        ))}
      </div>

      <article className="panel">
        <span className="eyebrow">INVITATIONS</span>
        <h2>En attente</h2>
        {invites.map((invitation) => (
          <div
            className="list-row"
            key={invitation.invitation_id}
          >
            <div>
              <b>{invitation.email}</b>
              <p>{invitation.role}</p>
            </div>
            <span>{invitation.expires_at ?? "—"}</span>
          </div>
        ))}
        {!invites.length && (
          <div className="empty">Aucune invitation.</div>
        )}
      </article>
    </section>
  );
}
