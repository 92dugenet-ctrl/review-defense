"""V5.7 Google Business Profile integration layer.

Official Google Business Profile REST/OAuth adapter with a deliberately narrow
boundary: authenticate, discover accounts/locations, read reviews, normalize
reviews into ReviewContext, and detect observed changes. No review reporting,
replying, deletion, or other external mutation is exposed here.

Network access is injectable for deterministic tests; the default transport
uses Python's standard library only.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol

from .review_workspace import ReviewContext

BUSINESS_MANAGE_SCOPE = "https://www.googleapis.com/auth/business.manage"
AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
ACCOUNT_API_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
LOCATION_API_BASE = "https://mybusinessbusinessinformation.googleapis.com/v1"
REVIEWS_API_BASE = "https://mybusiness.googleapis.com/v4"


class GoogleIntegrationError(RuntimeError):
    pass


class OAuthStateError(GoogleIntegrationError):
    pass


class GoogleAPIError(GoogleIntegrationError):
    def __init__(self, status: int, message: str):
        super().__init__(f"Google API error {status}: {message}")
        self.status = status
        self.message = message


class HTTPTransport(Protocol):
    def request(self, method: str, url: str, *, headers: Mapping[str, str] | None = None,
                body: bytes | None = None, timeout: float = 15.0) -> tuple[int, Mapping[str, str], bytes]: ...


class UrllibTransport:
    def request(self, method: str, url: str, *, headers=None, body=None, timeout=15.0):
        request = urllib.request.Request(url, data=body, headers=dict(headers or {}), method=method)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()
        except urllib.error.URLError as exc:
            raise GoogleIntegrationError(f"Google transport error: {exc.reason}") from exc


def _json(data: bytes) -> dict[str, Any]:
    if not data:
        return {}
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoogleIntegrationError("Google returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise GoogleIntegrationError("Google returned a non-object JSON response")
    return value


def _safe_error(body: bytes) -> str:
    try:
        value = _json(body)
        err = value.get("error", value)
        if isinstance(err, dict):
            return str(err.get("message") or err.get("status") or "unknown error")[:500]
        return str(err)[:500]
    except GoogleIntegrationError:
        return "unparseable error response"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@dataclass(frozen=True)
class OAuthAuthorization:
    state: str
    code_verifier: str
    authorization_url: str
    created_at: float


class OAuthStateManager:
    """Signed, short-lived state + PKCE verifier. State is opaque to Google."""
    def __init__(self, secret: bytes, *, ttl_seconds: int = 600, clock: Callable[[], float] = time.time):
        if not secret or len(secret) < 32:
            raise ValueError("OAuth state secret must contain at least 32 bytes")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.secret = secret
        self.ttl_seconds = ttl_seconds
        self.clock = clock

    def create(self, *, client_id: str, redirect_uri: str, extra_scopes: tuple[str, ...] = ()) -> OAuthAuthorization:
        if not client_id or not redirect_uri:
            raise ValueError("client_id and redirect_uri are required")
        verifier = _b64url(secrets.token_bytes(48))
        challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
        issued = int(self.clock())
        payload = f"{issued}.{_b64url(secrets.token_bytes(18))}"
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        state = f"{payload}.{signature}"
        scopes = (BUSINESS_MANAGE_SCOPE,) + tuple(extra_scopes)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(dict.fromkeys(scopes)),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        return OAuthAuthorization(
            state=state,
            code_verifier=verifier,
            authorization_url=AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(params),
            created_at=float(issued),
        )

    def verify(self, state: str) -> bool:
        try:
            issued_s, nonce, signature = state.split(".", 2)
            issued = int(issued_s)
        except (ValueError, AttributeError):
            raise OAuthStateError("invalid OAuth state")
        payload = f"{issued_s}.{nonce}"
        expected = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise OAuthStateError("invalid OAuth state signature")
        if self.clock() - issued > self.ttl_seconds:
            raise OAuthStateError("expired OAuth state")
        if self.clock() < issued - 30:
            raise OAuthStateError("OAuth state issued in the future")
        return True


@dataclass(frozen=True)
class OAuthTokenSet:
    access_token: str
    expires_at: float
    refresh_token: str | None = None
    scope: str | None = None
    token_type: str = "Bearer"

    def expired(self, *, now: float | None = None, leeway: int = 60) -> bool:
        return (time.time() if now is None else now) >= self.expires_at - leeway


class InMemoryTokenStore:
    """Reference store only. Production must use encrypted secret storage/KMS."""
    def __init__(self):
        self._tokens: dict[tuple[str, str], OAuthTokenSet] = {}

    def save(self, organization_id: str, connection_id: str, token: OAuthTokenSet) -> None:
        if not organization_id or not connection_id or not token.access_token:
            raise ValueError("organization_id, connection_id and access_token are required")
        self._tokens[(organization_id, connection_id)] = token

    def get(self, organization_id: str, connection_id: str) -> OAuthTokenSet | None:
        return self._tokens.get((organization_id, connection_id))

    def delete(self, organization_id: str, connection_id: str) -> None:
        self._tokens.pop((organization_id, connection_id), None)


class GoogleOAuthClient:
    def __init__(self, *, client_id: str, client_secret: str, transport: HTTPTransport | None = None,
                 token_endpoint: str = TOKEN_ENDPOINT, clock: Callable[[], float] = time.time):
        if not client_id or not client_secret:
            raise ValueError("Google OAuth client credentials are required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.transport = transport or UrllibTransport()
        self.token_endpoint = token_endpoint
        self.clock = clock

    def exchange_code(self, *, code: str, redirect_uri: str, code_verifier: str) -> OAuthTokenSet:
        return self._token_request({
            "grant_type": "authorization_code", "code": code,
            "redirect_uri": redirect_uri, "code_verifier": code_verifier,
        })

    def refresh(self, refresh_token: str) -> OAuthTokenSet:
        if not refresh_token:
            raise ValueError("refresh_token is required")
        return self._token_request({"grant_type": "refresh_token", "refresh_token": refresh_token})

    def _token_request(self, params: Mapping[str, str]) -> OAuthTokenSet:
        body = dict(params)
        body.update({"client_id": self.client_id, "client_secret": self.client_secret})
        status, _, raw = self.transport.request(
            "POST", self.token_endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            body=urllib.parse.urlencode(body).encode("utf-8"),
        )
        data = _json(raw) if raw else {}
        if status >= 400:
            raise GoogleAPIError(status, _safe_error(raw))
        access = data.get("access_token")
        expires = data.get("expires_in")
        if not isinstance(access, str) or not access or not isinstance(expires, (int, float)):
            raise GoogleIntegrationError("Google OAuth response missing access_token/expires_in")
        return OAuthTokenSet(
            access_token=access,
            expires_at=self.clock() + float(expires),
            refresh_token=data.get("refresh_token") or params.get("refresh_token"),
            scope=data.get("scope"), token_type=data.get("token_type", "Bearer"),
        )


@dataclass(frozen=True)
class GoogleAccount:
    name: str
    account_name: str | None
    account_type: str | None
    role: str | None


@dataclass(frozen=True)
class GoogleLocation:
    name: str
    location_name: str | None
    store_code: str | None = None
    language_code: str | None = None


@dataclass(frozen=True)
class ReviewSyncItem:
    review: ReviewContext
    fingerprint: str
    change: str  # NEW | UPDATED | UNCHANGED


@dataclass(frozen=True)
class ReviewSyncResult:
    items: tuple[ReviewSyncItem, ...]
    next_page_token: str | None = None


class ReviewCache:
    """Tenant-scoped observed-state cache; absence is never interpreted as deletion."""
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    @staticmethod
    def fingerprint(review: ReviewContext) -> str:
        raw = json.dumps({
            "rating": review.rating, "text": review.text, "author": review.author_display_name,
            "published_at": review.published_at, "updated_at": review.updated_at,
            "language": review.language,
        }, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def observe(self, review: ReviewContext) -> ReviewSyncItem:
        key = (review.organization_id, review.review_id)
        fp = self.fingerprint(review)
        old = self._data.get(key)
        change = "NEW" if old is None else ("UPDATED" if old != fp else "UNCHANGED")
        self._data[key] = fp
        return ReviewSyncItem(review, fp, change)

    def clear_organization(self, organization_id: str) -> None:
        for key in [k for k in self._data if k[0] == organization_id]:
            del self._data[key]


class GoogleBusinessProfileClient:
    """Read-only Google GBP adapter for accounts, locations and reviews."""
    def __init__(self, *, organization_id: str, access_token: str,
                 transport: HTTPTransport | None = None, timeout: float = 15.0):
        if not organization_id or not access_token:
            raise ValueError("organization_id and access_token are required")
        self.organization_id = organization_id
        self.access_token = access_token
        self.transport = transport or UrllibTransport()
        self.timeout = timeout

    def _get(self, url: str, params: Mapping[str, str] | None = None) -> dict[str, Any]:
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        status, _, raw = self.transport.request("GET", url, headers={
            "Authorization": f"Bearer {self.access_token}", "Accept": "application/json",
        }, timeout=self.timeout)
        if status >= 400:
            raise GoogleAPIError(status, _safe_error(raw))
        return _json(raw)

    def list_accounts(self, *, page_token: str | None = None) -> tuple[tuple[GoogleAccount, ...], str | None]:
        params = {"pageToken": page_token} if page_token else None
        data = self._get(f"{ACCOUNT_API_BASE}/accounts", params)
        accounts = tuple(GoogleAccount(
            name=a.get("name", ""), account_name=a.get("accountName"),
            account_type=a.get("type"), role=a.get("role"),
        ) for a in data.get("accounts", []) if a.get("name"))
        return accounts, data.get("nextPageToken")

    def list_locations(self, account_id: str, *, page_token: str | None = None,
                       read_mask: str = "name,locationName,storeCode,languageCode") -> tuple[tuple[GoogleLocation, ...], str | None]:
        account = self._resource_id(account_id, "accounts")
        params: dict[str, str] = {"readMask": read_mask}
        if page_token:
            params["pageToken"] = page_token
        data = self._get(f"{LOCATION_API_BASE}/accounts/{account}/locations", params)
        locations = tuple(GoogleLocation(
            name=l.get("name", ""), location_name=l.get("locationName"),
            store_code=l.get("storeCode"), language_code=l.get("languageCode"),
        ) for l in data.get("locations", []) if l.get("name"))
        return locations, data.get("nextPageToken")

    def list_reviews(self, account_id: str, location_id: str, *, page_token: str | None = None,
                     page_size: int | None = None, order_by: str | None = None) -> ReviewSyncResult:
        account = self._resource_id(account_id, "accounts")
        location = self._resource_id(location_id, "locations")
        params: dict[str, str] = {}
        if page_token:
            params["pageToken"] = page_token
        if page_size is not None:
            if not 1 <= page_size <= 50:
                raise ValueError("page_size must be between 1 and 50")
            params["pageSize"] = str(page_size)
        if order_by:
            params["orderBy"] = order_by
        data = self._get(f"{REVIEWS_API_BASE}/accounts/{account}/locations/{location}/reviews", params)
        items = []
        for raw in data.get("reviews", []):
            review = self._normalize_review(raw, location)
            items.append(review)
        return ReviewSyncResult(tuple(items), data.get("nextPageToken"))

    def get_review(self, account_id: str, location_id: str, review_id: str) -> ReviewContext:
        account = self._resource_id(account_id, "accounts")
        location = self._resource_id(location_id, "locations")
        rid = self._resource_id(review_id, "reviews")
        data = self._get(f"{REVIEWS_API_BASE}/accounts/{account}/locations/{location}/reviews/{rid}")
        return self._normalize_review(data, location)

    @staticmethod
    def _resource_id(value: str, prefix: str) -> str:
        if not value:
            raise ValueError(f"{prefix} id is required")
        value = value.rstrip("/")
        if "/" in value:
            if not value.startswith(prefix + "/"):
                raise ValueError(f"invalid {prefix} resource")
            value = value.split("/", 1)[1]
        if not value or "/" in value or value in {".", ".."}:
            raise ValueError(f"invalid {prefix} id")
        return value

    def _normalize_review(self, raw: Mapping[str, Any], location_id: str) -> ReviewContext:
        name = str(raw.get("name") or "")
        review_id = raw.get("reviewId") or (name.rsplit("/", 1)[-1] if name else None)
        if not review_id:
            raise GoogleIntegrationError("Google review missing reviewId/name")
        rating_map = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
        rating_raw = raw.get("starRating", 0)
        rating = rating_map.get(str(rating_raw).upper(), rating_raw if isinstance(rating_raw, int) else 0)
        if not 1 <= int(rating) <= 5:
            raise GoogleIntegrationError(f"invalid Google starRating for review {review_id}")
        reviewer = raw.get("reviewer") or {}
        return ReviewContext(
            review_id=str(review_id), organization_id=self.organization_id,
            location_id=location_id, author_display_name=reviewer.get("displayName"),
            rating=int(rating), text=str(raw.get("comment") or ""),
            published_at=str(raw.get("createTime") or ""),
            updated_at=raw.get("updateTime"), language=raw.get("languageCode"),
            source="GOOGLE", review_url=raw.get("reviewUrl"),
        )


@dataclass(frozen=True)
class GoogleMutationBoundary:
    """Explicit guard: V5.7 exposes no automatic Google mutation."""
    def submit_report(self, *_args, **_kwargs):
        raise RuntimeError("Google review reporting is not an automatic API action in V5.7; use the approved submission workflow")

    def reply_to_review(self, *_args, **_kwargs):
        raise RuntimeError("Review replies are outside the Review Defense automated action boundary")
