import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ApiError, api } from "@/services/api/client";
import { useAuth } from "@/auth/AuthContext";
import type { AdminMember, InvitationResponse } from "@/types/api";

const roles = ["ADMIN", "ANALYST", "CLIENT", "VIEWER"] as const;

export function AdminPage() {
  const { user } = useAuth();
  const [members, setMembers] = useState<AdminMember[]>([]);
  const [email, setEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<(typeof roles)[number]>("CLIENT");
  const [invitation, setInvitation] = useState<InvitationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const canAdmin = user?.role === "OWNER" || user?.role === "ADMIN";

  async function load() {
    setLoading(true); setError("");
    try {
      const response = await api.get<{ items: AdminMember[] }>("/v1/organization/members");
      setMembers(response.items ?? []);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Impossible de charger les membres.");
    } finally { setLoading(false); }
  }

  useEffect(() => { if (canAdmin) void load(); else setLoading(false); }, [canAdmin]);

  async function invite() {
    if (!email.trim()) return;
    setBusy("invite"); setError(""); setMessage(""); setInvitation(null);
    try {
      const response = await api.post<InvitationResponse>("/v1/organization/invitations", { email: email.trim(), role: inviteRole });
      setInvitation(response); setEmail(""); setMessage("Invitation créée. Le jeton est affiché une seule fois.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Création de l’invitation impossible.");
    } finally { setBusy(""); }
  }

  async function changeRole(member: AdminMember, role: string) {
    setBusy("role:" + member.user_id); setError(""); setMessage("");
    try {
      await api.post("/v1/organization/members/" + member.user_id + "/role", { role });
      setMessage("Rôle de " + member.email + " mis à jour."); await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Modification du rôle impossible.");
    } finally { setBusy(""); }
  }

  async function revokeSessions(member: AdminMember) {
    if (!window.confirm("Révoquer toutes les sessions de " + member.email + " ?")) return;
    setBusy("revoke:" + member.user_id); setError(""); setMessage("");
    try {
      await api.post("/v1/auth/revoke-all", { user_id: member.user_id });
      setMessage("Sessions révoquées pour " + member.email + ".");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Révocation impossible.");
    } finally { setBusy(""); }
  }

  if (!canAdmin) return (
    <section className="admin-page">
      <div className="admin-denied">
        <span className="eyebrow">REVIEW DEFENSE · ADMINISTRATION</span>
        <h1>Accès réservé</h1>
        <p>Cette surface est réservée aux propriétaires et administrateurs de l’organisation.</p>
        <a href="/app/dashboard">Retour au tableau de bord →</a>
      </div>
    </section>
  );

  return (
    <section className="admin-page">
      <div className="admin-hero">
        <div><span className="eyebrow">REVIEW DEFENSE · ADMINISTRATION</span><h1>Gouverner le workspace.</h1><p>Gérez les membres, les rôles et les accès sans contourner les contrôles du backend.</p></div>
        <Button variant="secondary" onClick={() => void load()} disabled={loading}>{loading ? "Actualisation…" : "Actualiser"}</Button>
      </div>
      {error && <div className="dashboard-error" role="alert"><strong>Action impossible</strong><span>{error}</span></div>}
      {message && <div className="billing-status">{message}</div>}

      <div className="admin-grid">
        <article className="dashboard-surface dashboard-card">
          <div className="dashboard-section-heading"><div><span>MEMBRES</span><h2>Accès au workspace</h2></div><strong>{loading ? "…" : members.length}</strong></div>
          <div className="admin-member-list">
            {loading ? <div className="dashboard-empty">Chargement des membres…</div> : members.length ? members.map((member) => (
              <div className="admin-member-row" key={member.user_id}>
                <div className="admin-member-identity"><span className="admin-avatar">{member.email.slice(0, 2).toUpperCase()}</span><div><strong>{member.email}</strong><small>{member.user_id}</small></div></div>
                <div className="admin-member-actions">
                  <select aria-label={"Rôle de " + member.email} value={member.role} disabled={member.user_id === user?.user_id || busy === "role:" + member.user_id} onChange={(event) => void changeRole(member, event.target.value)}>
                    <option value="OWNER">OWNER</option>{roles.map((role) => <option key={role} value={role}>{role}</option>)}
                  </select>
                  <button className="module-secondary" disabled={busy === "revoke:" + member.user_id} onClick={() => void revokeSessions(member)}>{busy === "revoke:" + member.user_id ? "Révocation…" : "Révoquer sessions"}</button>
                </div>
              </div>
            )) : <div className="dashboard-empty"><strong>Aucun membre</strong><span>Invitez votre premier collaborateur.</span></div>}
          </div>
        </article>

        <article className="dashboard-surface dashboard-card">
          <div className="dashboard-section-heading"><div><span>INVITATION</span><h2>Ajouter un membre</h2></div></div>
          <div className="admin-form">
            <label>Email<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="collaborateur@entreprise.fr" /></label>
            <label>Rôle<select value={inviteRole} onChange={(e) => setInviteRole(e.target.value as (typeof roles)[number])}>{roles.map((role) => <option key={role}>{role}</option>)}</select></label>
            <Button onClick={() => void invite()} disabled={!email.trim() || busy === "invite"}>{busy === "invite" ? "Création…" : "Créer l’invitation"}</Button>
          </div>
          {invitation?.invitation_token && <div className="admin-token"><strong>Jeton d’invitation</strong><code>{invitation.invitation_token}</code><button className="module-secondary" onClick={() => void navigator.clipboard?.writeText(invitation.invitation_token || "")}>Copier</button></div>}
        </article>
      </div>

      <article className="dashboard-surface dashboard-card admin-security">
        <div className="dashboard-section-heading"><div><span>SÉCURITÉ</span><h2>Contrôles d’accès</h2></div></div>
        <div className="admin-security-grid">
          <div><strong>Rôles persistants</strong><span>Les changements sont appliqués au membership backend et aux sessions actives.</span></div>
          <div><strong>Révocation globale</strong><span>Une révocation invalide toutes les sessions du membre ciblé.</span></div>
          <div><strong>Contrôle humain</strong><span>Aucune action d’administration ne modifie automatiquement les dossiers métier.</span></div>
        </div>
      </article>
    </section>
  );
}
