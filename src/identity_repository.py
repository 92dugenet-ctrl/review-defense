""""V6.2 PostgreSQL identity/session repository extensions."""
from __future__ import annotations
import json
import uuid
from .postgres_api_repository import PostgresAPIRepository

class IdentityRepository(PostgresAPIRepository):
    def update_password(self, organization_id: str, user_id: str, password_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET password_hash=%s,password_changed_at=now(),updated_at=now() WHERE id=%s", (password_hash,user_id))
                cur.execute("UPDATE api_sessions SET revoked_at=now() WHERE organization_id=%s AND user_id=%s AND revoked_at IS NULL", (organization_id,user_id))

    def revoke_all_sessions(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_sessions SET revoked_at=now() WHERE organization_id=%s AND user_id=%s AND revoked_at IS NULL", (organization_id,user_id))

    def revoke_other_sessions(self, organization_id: str, user_id: str, keep_token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_sessions SET revoked_at=now() WHERE organization_id=%s AND user_id=%s AND token_hash<>%s AND revoked_at IS NULL", (organization_id,user_id,keep_token_hash))

    def update_role(self, organization_id: str, user_id: str, role: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE memberships SET role=%s WHERE organization_id=%s AND user_id=%s", (role,organization_id,user_id))
                cur.execute("UPDATE api_sessions SET role=%s,revoked_at=now() WHERE organization_id=%s AND user_id=%s AND revoked_at IS NULL", (role,organization_id,user_id))

    def create_invitation(self, organization_id, email, role, token_hash, invited_by, expires_at):
        iid = str(uuid.uuid4())
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO organization_invitations(invitation_id,organization_id,email,role,token_hash,invited_by,expires_at) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING invitation_id", (iid,organization_id,email,role,token_hash,invited_by,expires_at))
                return str(cur.fetchone()[0])

    def accept_invitation(self, organization_id, token_hash, user_id, password_hash, email, role):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT invitation_id,email,role,expires_at,accepted_at,revoked_at FROM organization_invitations WHERE organization_id=%s AND token_hash=%s FOR UPDATE", (organization_id,token_hash))
                row = cur.fetchone()
                if not row: return False
                iid, em, inv_role, expires, accepted, revoked = row
                cur.execute("UPDATE users SET password_hash=%s,password_changed_at=now(),updated_at=now() WHERE id=%s", (password_hash,user_id))
                cur.execute("INSERT INTO memberships(organization_id,user_id,role) VALUES(%s,%s,%s) ON CONFLICT(organization_id,user_id) DO UPDATE SET role=excluded.role", (organization_id,user_id,inv_role))
                cur.execute("UPDATE organization_invitations SET accepted_at=now() WHERE invitation_id=%s", (iid,))
                return True

    def security_event(self, organization_id, actor_user_id, event_type, target_user_id=None, metadata=None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO security_events(organization_id,actor_user_id,event_type,target_user_id,metadata) VALUES(%s,%s,%s,%s,%s::jsonb)", (organization_id,actor_user_id,event_type,target_user_id,json.dumps(metadata or {},sort_keys=True)))

    def get_mfa_state(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT mfa_enabled,mfa_secret_enc FROM users WHERE id=%s", (user_id,))
                return cur.fetchone()

    def set_mfa_secret(self, organization_id: str, user_id: str, secret_enc: str, enabled: bool):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET mfa_secret_enc=%s,mfa_enabled=%s,mfa_enabled_at=CASE WHEN %s THEN now() ELSE NULL END WHERE id=%s", (secret_enc,enabled,enabled,user_id))

    def disable_mfa(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET mfa_enabled=false,mfa_secret_enc=NULL,mfa_enabled_at=NULL WHERE id=%s", (user_id,))

    def create_recovery_token(self, organization_id: str, user_id: str, token_hash: str, expires_at: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO password_recovery_tokens(organization_id,user_id,token_hash,expires_at) VALUES(%s,%s,%s,%s)", (organization_id,user_id,token_hash,expires_at))

    def get_recovery_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT recovery_id,organization_id,user_id,expires_at,used_at FROM password_recovery_tokens WHERE organization_id=%s AND token_hash=%s", (organization_id,token_hash))
                return cur.fetchone()

    def consume_recovery_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE password_recovery_tokens SET used_at=now() WHERE organization_id=%s AND token_hash=%s AND used_at IS NULL", (organization_id,token_hash))
                return cur.rowcount == 1

    def get_user_by_id(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT u.id,u.email,u.password_hash,m.role FROM users u JOIN memberships m ON m.user_id=u.id WHERE m.organization_id=%s AND u.id=%s", (organization_id,user_id))
                return cur.fetchone()

    def get_session_by_token_hash(self, token_hash: str):
        """Load a persisted session before tenant context is known.

        The token hash is the only lookup key and the raw bearer token is never
        persisted. The database function is intentionally narrow and returns
        only the session row needed to establish the authenticated tenant.
        """
        with self.transaction_without_tenant() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT token_hash,user_id,organization_id,role,expires_at,revoked_at FROM lookup_api_session_by_token_hash(%s)", (token_hash,))
                return cur.fetchone()
