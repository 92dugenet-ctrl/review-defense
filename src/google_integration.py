"""V5.7 Google Business Profile integration layer.

Framework-neutral OAuth 2.0 + REST adapter for the official Google Business
Profile APIs. Network transport is injectable for deterministic tests.

This module is read/synchronization oriented: it can discover authorized
accounts/locations and import reviews into the Review Defense domain, but it
never reports/removes reviews or performs another external mutation.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .review_workspace import ReviewContext

GOOGLE_SCOPE = "https://www.googleapis.com/auth/business.manage"
AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
ACCOUNT_API = "https://mybusinessaccountmanagement.googleapis.com/v1"
BUSINESS_API = "https://mybusinessbusinessinformation.googleapis.com/v1"
REVIEWS_API = "https://mybusiness.googleapis.com/v4"
MAX_CACHE_SECONDS = 30 * 24 * 60 * 60


class GoogleIntegrationError(RuntimeError):
    pass


class OAuthStateError(GoogleIntegrationError):
    pass


class GoogleAPIError(GoogleIntegrationError):
    def __init__(self, status: int, message: str, body: str = ""):
        super().__init__(f"Google API HTTP {status}: {message}")
        self.status = status
        self.body = body


@dataclass(frozen=True)
class OAuthClientConfig:
    client_id: str
    redirect_uri: str
    client_secret: str | None = None
    scope: str = GOOGLE_SCOPE


@dataclass(frozen=True)
class OAuthState:
    value: str
    code_verifier: str
    created_at: float


class OAuthStateStore:
    def __init__(self, *, ttl_seconds: int = 600, clock: Callable[[], float] | None = None):
        self.ttl_seconds = ttl_seconds
        self.clock = clock or time.time
        self._items: dict[str, OAuthState] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _pkce_verifier() -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()

    def create(self) -> OAuthState:
        state = secrets.token_urlsafe(32)
        item = OAuthState(state, self._pkce_verifier(), self.clock())
        with self._lock:
            self._items[state] = item
        return item

    def consume(self, state: str) -> OAuthState:
        if not state:
            raise OAuthStateError("missing OAuth state")
        with self._lock:
            item = self._items.pop(state, None)
        if item is None:
            raise OAuthStateError("unknown or already-consumed OAuth state")
        if self.clock() - item.created_at > self.ttl_seconds:
            raise OAuthStateError("expired OAuth state")
        return item


@dataclass(frozen=True)
class GoogleToken:
    access_token: str
    refresh_token: str | None
    expires_at: float
    scope: str = GOOGLE_SCOPE
    token_type: str = "Bearer"

    def expired(self, *, now: float | None = None, leeway: int = 60) -> bool:
        return (now or time.time()) >= self.expires_at - leeway


class TokenStore(Protocol):
    def save(self, organization_id: str, token: GoogleToken) -> None: ...
    def get(self, organization_id: str) -> GoogleToken | None: ...
    def delete(self, organization_id: str) -> None: ...


class InMemoryTokenStore:
    def __init__(self):
        self._tokens: dict[str, GoogleToken] = {}
        self._lock = threading.Lock()

    def save(self, organization_id: str, token: GoogleToken) -> None:
        if not organization_id:
            raise ValueError("organization_id is required")
        with self._lock:
            self._tokens[organization_id] = token

    def get(self, organization_id: str) -> GoogleToken | None:
        with self._lock:
            return self._tokens.get(organization_id)

    def delete(self, organization_id: str) -> None:
        with self._lock:
            self._tokens.pop(organization_id, None)


class HTTPTransport(Protocol):
    def request(self, method: str, url: str, *, headers: Mapping[str, str],
                body: bytes | None = None, timeout: float = 20.0) -> tuple[int, Mapping[str, str], bytes]: ...


class UrllibTransport:
    def request(self, method: str, url: str, *, headers: Mapping[str, str],
                body: bytes | None = None, timeout: float = 20.0):
        req = Request(url, data=body, headers=dict(headers), method=method)
        try:
            with urlopen(req, timeout=timeout) as response:
                return response.status, dict(response.headers), response.read()
        except HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()
        except URLError as exc:
            raise GoogleIntegrationError(f"Google network error: {exc.reason}") from exc


def _json_bytes(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":")).encode()


def _parse_json(body: bytes) -> dict[str, Any]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoogleIntegrationError("Google returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise GoogleIntegrationError("Google returned an unexpected JSON shape")
    return value


class GoogleOAuthClient:
    def __init__(self, config: OAuthClientConfig, *, states: OAuthStateStore | None = None,
                 transport: HTTPTransport | None = None, clock: Callable[[], float] | None = None):
        if not config.client_id or not config.redirect_uri:
            raise ValueError("client_id and redirect_uri are required")
        self.config = config
        self.states = states or OAuthStateStore(clock=clock)
        self.transport = transport or UrllibTransport()
        self.clock = clock or time.time

    def authorization_url(self, *, login_hint: str | None = None) -> tuple[str, OAuthState]:
        state = self.states.create()
        digest = hashlib.sha256(state.code_verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.config.scope,
            "access_type": "offline",
            "prompt": "consent",
            "state": state.value,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        if login_hint:
            params["login_hint"] = login_hint
        return AUTHORIZATION_ENDPOINT + "?" + urlencode(params), state

    def exchange_code(self, *, code: str, state: str) -> GoogleToken:
        item = self.states.consume(state)
        form = {
            "code": code,
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": item.code_verifier,
        }
        if self.config.client_secret:
            form["client_secret"] = self.config.client_secret
        status, _, body = self.transport.request(
            "POST", TOKEN_ENDPOINT,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=urlencode(form).encode(),
        )
        if status >= 400:
            raise GoogleAPIError(status, "OAuth token exchange failed", body.decode("utf-8", "replace"))
        data = _parse_json(body)
        return GoogleToken(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token"),
            expires_at=self.clock() + int(data.get("expires_in", 3600)),
            scope=str(data.get("scope", self.config.scope)),
            token_type=str(data.get("token_type", "Bearer")),
        )

    def refresh(self, token: GoogleToken) -> GoogleToken:
        if not token.refresh_token:
            raise GoogleIntegrationError("no refresh token available; user consent is required again")
        form = {
            "client_id": self.config.client_id,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        }
        if self.config.client_secret:
            form["client_secret"] = self.config.client_secret
        status, _, body = self.transport.request(
            "POST", TOKEN_ENDPOINT,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=urlencode(form).encode(),
        )
        if status >= 400:
            raise GoogleAPIError(status, "OAuth token refresh failed", body.decode("utf-8", "replace"))
        data = _parse_json(body)
        return GoogleToken(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token") or token.refresh_token,
            expires_at=self.clock() + int(data.get("expires_in", 3600)),
            scope=str(data.get("scope", token.scope)),
            token_type=str(data.get("token_type", token.token_type)),
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
    title: str | None
    store_code: str | None
    website_uri: str | None


@dataclass(frozen=True)
class SyncResult:
    organization_id: str
    location_name: str
    fetched: int
    changed: int
    unchanged: int
    reviews: tuple[ReviewContext, ...]


@dataclass(frozen=True)
class CachedReview:
    review: ReviewContext
    fetched_at: float
    fingerprint: str


class ReviewCache:
    """Tenant-bound, expiring cache. It never stores content beyond 30 days."""
    def __init__(self, *, ttl_seconds: int = MAX_CACHE_SECONDS, clock: Callable[[], float] | None = None):
        if ttl_seconds <= 0 or ttl_seconds > MAX_CACHE_SECONDS:
            raise ValueError("cache TTL must be positive and no more than 30 days")
        self.ttl_seconds = ttl_seconds
        self.clock = clock or time.time
        self._items: dict[tuple[str, str], CachedReview] = {}
        self._lock = threading.Lock()

    @staticmethod
    def fingerprint(review: ReviewContext) -> str:
        payload = {
            "id": review.review_id, "location": review.location_id,
            "rating": review.rating, "text": review.text,
            "author": review.author_display_name, "published": review.published_at,
            "updated": review.updated_at,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def put(self, review: ReviewContext) -> bool:
        key = (review.organization_id, review.review_id)
        item = CachedReview(review, self.clock(), self.fingerprint(review))
        with self._lock:
            previous = self._items.get(key)
            changed = previous is None or previous.fingerprint != item.fingerprint
            self._items[key] = item
        return changed

    def get(self, organization_id: str, review_id: str) -> ReviewContext | None:
        with self._lock:
            item = self._items.get((organization_id, review_id))
            if item is None:
                return None
            if self.clock() - item.fetched_at > self.ttl_seconds:
                del self._items[(organization_id, review_id)]
                return None
            return item.review

    def purge_expired(self) -> int:
        now = self.clock()
        with self._lock:
            expired = [k for k, v in self._items.items() if now - v.fetched_at > self.ttl_seconds]
            for key in expired:
                del self._items[key]
            return len(expired)


class GoogleBusinessProfileClient:
    """Official GBP read adapter for accounts, locations and reviews."""
    def __init__(self, *, organization_id: str, token: GoogleToken,
                 transport: HTTPTransport | None = None, oauth: GoogleOAuthClient | None = None,
                 token_store: TokenStore | None = None, clock: Callable[[], float] | None = None):
        if not organization_id:
            raise ValueError("organization_id is required")
        self.organization_id = organization_id
        self.token = token
        self.transport = transport or UrllibTransport()
        self.oauth = oauth
        self.token_store = token_store
        self.clock = clock or time.time

    def _access_token(self) -> str:
        if self.token.expired(now=self.clock()):
            if not self.oauth:
                raise GoogleIntegrationError("access token expired and no OAuth refresh client configured")
            self.token = self.oauth.refresh(self.token)
            if self.token_store:
                self.token_store.save(self.organization_id, self.token)
        return self.token.access_token

    def _get(self, base: str, path: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        query = urlencode([(k, v) for k, v in (params or {}).items() if v is not None])
        url = base.rstrip("/") + "/" + path.lstrip("/")
        if query:
            url += "?" + query
        status, _, body = self.transport.request(
            "GET", url,
            headers={"Authorization": f"Bearer {self._access_token()}", "Accept": "application/json"},
        )
        if status >= 400:
            raise GoogleAPIError(status, "Google Business Profile request failed", body.decode("utf-8", "replace"))
        return _parse_json(body)

    def list_accounts(self) -> tuple[GoogleAccount, ...]:
        accounts: list[GoogleAccount] = []
        page_token: str | None = None
        while True:
            data = self._get(ACCOUNT_API, "accounts", {"pageSize": 20, "pageToken": page_token})
            for item in data.get("accounts", []):
                accounts.append(GoogleAccount(item.get("name", ""), item.get("accountName"), item.get("type"), item.get("role")))
            page_token = data.get("nextPageToken")
            if not page_token:
                return tuple(accounts)

    def list_locations(self, account_name: str) -> tuple[GoogleLocation, ...]:
        if not account_name.startswith("accounts/"):
            raise ValueError("invalid Google account resource name")
        locations: list[GoogleLocation] = []
        page_token: str | None = None
        while True:
            data = self._get(BUSINESS_API, f"{account_name}/locations", {
                "pageSize": 100, "pageToken": page_token,
                "readMask": "name,title,storeCode,websiteUri",
            })
            for item in data.get("locations", []):
                locations.append(GoogleLocation(item.get("name", ""), item.get("title"), item.get("storeCode"), item.get("websiteUri")))
            page_token = data.get("nextPageToken")
            if not page_token:
                return tuple(locations)

    def list_reviews_raw(self, location_name: str) -> tuple[dict[str, Any], ...]:
        if not location_name.startswith("accounts/") or "/locations/" not in location_name:
            raise ValueError("invalid Google location resource name")
        reviews: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            data = self._get(REVIEWS_API, f"{location_name}/reviews", {"pageSize": 50, "pageToken": page_token, "orderBy": "updateTime desc"})
            reviews.extend(x for x in data.get("reviews", []) if isinstance(x, dict))
            page_token = data.get("nextPageToken")
            if not page_token:
                return tuple(reviews)

    def get_review_raw(self, review_name: str) -> dict[str, Any]:
        if not review_name.startswith("accounts/"):
            raise ValueError("invalid Google review resource name")
        return self._get(REVIEWS_API, review_name)

    def list_reviews(self, location_id: str | None = None) -> tuple[ReviewContext, ...]:
        if not location_id:
            raise ValueError("location_id is required for review listing")
        raw = self.list_reviews_raw(location_id)
        return tuple(self._to_review_context(location_id, item) for item in raw)

    def get_review(self, review_id: str) -> ReviewContext:
        item = self.get_review_raw(review_id)
        location_id = "/".join(review_id.split("/")[:4])
        return self._to_review_context(location_id, item)

    def get_status(self, review_id: str) -> str:
        self.get_review_raw(review_id)
        return "PRESENT"

    def _to_review_context(self, location_name: str, item: Mapping[str, Any]) -> ReviewContext:
        review_name = str(item.get("name", ""))
        reviewer = item.get("reviewer") or {}
        rating_map = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
        rating_raw = str(item.get("starRating", "UNSPECIFIED"))
        rating = rating_map.get(rating_raw)
        if rating is None:
            raise GoogleIntegrationError(f"unsupported Google starRating: {rating_raw}")
        create_time = str(item.get("createTime") or "")
        update_time = item.get("updateTime")
        location_id = location_name
        return ReviewContext(
            review_id=review_name,
            organization_id=self.organization_id,
            location_id=location_id,
            author_display_name=reviewer.get("displayName"),
            rating=rating,
            text=str(item.get("comment") or ""),
            published_at=create_time,
            updated_at=str(update_time) if update_time else None,
            language=reviewer.get("languageCode"),
            source="GOOGLE",
            review_url=None,
        )

    def sync_reviews(self, *, location_id: str, cache: ReviewCache) -> SyncResult:
        reviews = self.list_reviews(location_id)
        changed = 0
        for review in reviews:
            if cache.put(review):
                changed += 1
        return SyncResult(self.organization_id, location_id, len(reviews), changed, len(reviews) - changed, reviews)

    # Deliberately no report/delete/reply method in V5.7. External mutations
    # remain behind the approved submission workflow in later application code.
