import json

import pytest

from src.google_business_profile import (
    ACCOUNT_API_BASE, AUTHORIZATION_ENDPOINT, BUSINESS_MANAGE_SCOPE,
    LOCATION_API_BASE, REVIEWS_API_BASE, GoogleAPIError, GoogleBusinessProfileClient,
    GoogleMutationBoundary, GoogleOAuthClient, InMemoryTokenStore, OAuthStateError,
    OAuthStateManager, OAuthTokenSet, ReviewCache,
)


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.responses = []

    def queue(self, status, body):
        self.responses.append((status, {"content-type": "application/json"}, json.dumps(body).encode()))

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected network call")
        return self.responses.pop(0)


def test_oauth_state_uses_pkce_and_is_signed():
    clock = [1000.0]
    mgr = OAuthStateManager(b"x" * 32, clock=lambda: clock[0])
    auth = mgr.create(client_id="cid", redirect_uri="https://app/callback")
    assert auth.authorization_url.startswith(AUTHORIZATION_ENDPOINT + "?")
    assert "business.manage" in auth.authorization_url
    assert "code_challenge=" in auth.authorization_url
    assert "code_challenge_method=S256" in auth.authorization_url
    assert mgr.verify(auth.state)
    with pytest.raises(OAuthStateError):
        mgr.verify(auth.state[:-1] + ("0" if auth.state[-1] != "0" else "1"))
    clock[0] = 2000
    with pytest.raises(OAuthStateError):
        mgr.verify(auth.state)


def test_oauth_exchange_and_refresh_preserve_refresh_token():
    fake = FakeTransport()
    fake.queue(200, {"access_token": "a", "expires_in": 3600, "refresh_token": "r", "scope": BUSINESS_MANAGE_SCOPE})
    fake.queue(200, {"access_token": "b", "expires_in": 1800})
    client = GoogleOAuthClient(client_id="cid", client_secret="secret", transport=fake, clock=lambda: 100)
    first = client.exchange_code(code="code", redirect_uri="https://app/cb", code_verifier="verifier")
    second = client.refresh(first.refresh_token)
    assert first.refresh_token == second.refresh_token == "r"
    assert fake.calls[0][0] == "POST" and fake.calls[1][0] == "POST"


def test_token_store_is_tenant_scoped():
    store = InMemoryTokenStore()
    token = OAuthTokenSet("a", 9999, "r")
    store.save("org-a", "google-1", token)
    assert store.get("org-a", "google-1") == token
    assert store.get("org-b", "google-1") is None
    store.delete("org-a", "google-1")
    assert store.get("org-a", "google-1") is None


def test_list_accounts_uses_current_account_management_api():
    fake = FakeTransport()
    fake.queue(200, {"accounts": [{"name": "accounts/123", "accountName": "Acme", "type": "LOCATION_GROUP", "role": "OWNER"}]})
    client = GoogleBusinessProfileClient(organization_id="org-a", access_token="tok", transport=fake)
    accounts, token = client.list_accounts()
    assert accounts[0].name == "accounts/123"
    assert token is None
    assert fake.calls[0][1] == f"{ACCOUNT_API_BASE}/accounts"
    assert fake.calls[0][2]["headers"]["Authorization"] == "Bearer tok"


def test_list_locations_and_reviews_normalize_to_review_context():
    fake = FakeTransport()
    fake.queue(200, {"locations": [{"name": "locations/456", "locationName": "Acme Paris", "storeCode": "P1", "languageCode": "fr"}]})
    fake.queue(200, {"reviews": [{
        "name": "accounts/123/locations/456/reviews/789", "reviewId": "789",
        "reviewer": {"displayName": "Jean"}, "starRating": "FIVE",
        "comment": "Service excellent", "createTime": "2026-09-20T10:00:00Z",
        "updateTime": "2026-09-20T11:00:00Z", "languageCode": "fr"
    }], "nextPageToken": "next"})
    client = GoogleBusinessProfileClient(organization_id="org-a", access_token="tok", transport=fake)
    locs, _ = client.list_locations("accounts/123")
    result = client.list_reviews("accounts/123", "locations/456", page_size=10)
    assert locs[0].location_name == "Acme Paris"
    assert result.items[0].review_id == "789"
    assert result.items[0].rating == 5
    assert result.items[0].author_display_name == "Jean"
    assert result.next_page_token == "next"
    assert fake.calls[1][1].startswith(f"{REVIEWS_API_BASE}/accounts/123/locations/456/reviews?")


def test_review_cache_detects_observed_changes_without_inferring_deletion():
    fake = FakeTransport()
    fake.queue(200, {"reviews": [{"name": "accounts/a/locations/l/reviews/r", "reviewId": "r", "reviewer": {"displayName": "J"}, "starRating": "FOUR", "comment": "OK", "createTime": "2026-01-01T00:00:00Z"}]})
    client = GoogleBusinessProfileClient(organization_id="org-a", access_token="tok", transport=fake)
    review = client.list_reviews("a", "l").items[0]
    cache = ReviewCache()
    assert cache.observe(review).change == "NEW"
    assert cache.observe(review).change == "UNCHANGED"
    changed = review.__class__(**{**review.__dict__, "text": "OK maintenant"})
    assert cache.observe(changed).change == "UPDATED"


def test_tenant_isolation_in_cache():
    cache = ReviewCache()
    fake = FakeTransport()
    fake.queue(200, {"reviews": [{"name": "accounts/a/locations/l/reviews/r", "reviewId": "r", "reviewer": {}, "starRating": "FOUR", "comment": "OK", "createTime": "2026-01-01T00:00:00Z"}]})
    a = GoogleBusinessProfileClient(organization_id="org-a", access_token="tok", transport=fake).list_reviews("a", "l").items[0]
    cache.observe(a)
    b = a.__class__(**{**a.__dict__, "organization_id": "org-b"})
    assert cache.observe(b).change == "NEW"


def test_api_errors_do_not_leak_access_token():
    fake = FakeTransport()
    fake.queue(403, {"error": {"status": "PERMISSION_DENIED", "message": "forbidden"}})
    client = GoogleBusinessProfileClient(organization_id="org-a", access_token="SUPERSECRET", transport=fake)
    with pytest.raises(GoogleAPIError) as exc:
        client.list_accounts()
    assert "SUPERSECRET" not in str(exc.value)
    assert exc.value.status == 403


def test_resource_validation_blocks_cross_resource_paths():
    client = GoogleBusinessProfileClient(organization_id="org-a", access_token="tok", transport=FakeTransport())
    with pytest.raises(ValueError):
        client.list_locations("locations/123")
    with pytest.raises(ValueError):
        client.list_reviews("accounts/1", "../../locations/2")


def test_mutation_boundary_is_explicitly_disabled():
    boundary = GoogleMutationBoundary()
    with pytest.raises(RuntimeError):
        boundary.submit_report("case")
    with pytest.raises(RuntimeError):
        boundary.reply_to_review("review", "hello")
