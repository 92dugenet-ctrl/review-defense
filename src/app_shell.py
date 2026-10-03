"""Contrat historique d'accès aux écrans frontend.

ROUTES et ROLE_ACCESS décrivent les écrans et rôles de l'ancien shell.
Ce contrôle d'affichage ne remplace jamais l'autorisation serveur :
les endpoints API doivent vérifier eux-mêmes identité, tenant et rôle.
"""
from dataclasses import dataclass

ROUTES = {
    "/": "dashboard",
    "/cases": "cases",
    "/cases/:id": "case_workspace",
    "/reviews": "reviews",
    "/reviews/:id": "review_intelligence_workspace",
    "/evidence": "evidence",
    "/policies": "policies",
    "/policies/:id": "policy_intelligence_workspace",
    "/approvals": "approvals",
    "/submissions": "submissions",
    "/appeals": "appeals",
    "/outcomes": "outcome_tracking",
    "/submissions/:id/outcomes": "submission_outcome_tracking",
    "/alerts": "alerts",
    "/alerts/:id": "alert_detail",
    "/analytics": "analytics",
    "/audit": "audit",
    "/settings": "settings",
}

ROLE_ACCESS = {
    "OWNER": set(ROUTES),
    "ADMIN": set(ROUTES),
    "ANALYST": set(ROUTES) - {"/settings"},
    "CLIENT": {"/", "/cases", "/cases/:id", "/reviews", "/reviews/:id", "/evidence", "/policies/:id", "/alerts", "/alerts/:id", "/analytics"},
    "VIEWER": {"/", "/cases", "/cases/:id", "/reviews", "/reviews/:id", "/analytics"},
}

@dataclass(frozen=True)
class SessionContext:
    user_id: str
    organization_id: str
    role: str


def can_access(session: SessionContext, route: str) -> bool:
    """Indique si le rôle peut afficher une route de l'ancien shell."""
    if session.role not in ROLE_ACCESS:
        return False
    return route in ROLE_ACCESS[session.role]
