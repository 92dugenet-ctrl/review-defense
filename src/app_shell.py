"""V4.1 frontend application-shell reference: route/role contracts only."""
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
    if session.role not in ROLE_ACCESS:
        return False
    return route in ROLE_ACCESS[session.role]
