import io
import json
from datetime import datetime, timezone

from src.api_server import ReviewDefenseAPI, User, _review_from_row


class ReviewRepository:
    def __init__(self):
        self.rows = [[
            "persisted-review",
            "org-a",
            "location-1",
            "Client persistant",
            1,
            "Commande incomplète et service très mauvais.",
            datetime(2026, 9, 23, 10, 30, tzinfo=timezone.utc),
            None,
            "fr",
            "GOOGLE",
            "https://example.invalid/review/persisted-review",
        ]]

    def list_reviews(self, organization_id):
        assert organization_id == "org-a"
        return self.rows

    def get_review(self, organization_id, review_id):
        for row in self.rows:
            if row[0] == review_id:
                return row
        return None

    def create_case_persistent(self, organization_id, case_id, review_id, status, actor_user_id):
        assert organization_id == "org-a"
        assert review_id == "persisted-review"
        assert status == "ANALYZING"
        return (case_id, organization_id, review_id, status, None, None, None, None)


def call(app, method, path):
    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_LENGTH": "0",
        "wsgi.input": io.BytesIO(b""),
    }
    out = {}

    def start_response(status, headers):
        out["status"] = status
        out["headers"] = headers

    payload = b"".join(app(env, start_response))
    return out["status"], json.loads(payload)


def test_persistent_review_row_is_converted_to_api_contract():
    row = ReviewRepository().rows[0]
    review = _review_from_row(row)
    assert review.review_id == "persisted-review"
    assert review.organization_id == "org-a"
    assert review.rating == 1
    assert review.text.startswith("Commande incomplète")
    assert review.published_at == "2026-09-23T10:30:00+00:00"


def test_get_reviews_hydrates_persistent_rows_into_the_api_store():
    app = ReviewDefenseAPI()
    app.repository = ReviewRepository()
    app._auth = lambda environ: User(
        "user-a", "org-a", "admin@example.com", "hash", "ADMIN"
    )

    status, data = call(app, "GET", "/v1/reviews")

    assert status == "200 OK"
    assert data["count"] == 1
    assert data["items"][0]["review_id"] == "persisted-review"
    assert data["items"][0]["rating"] == 1
    assert ("org-a", "persisted-review") in app.store.reviews


def test_get_single_review_falls_back_to_persistent_repository():
    app = ReviewDefenseAPI()
    app.repository = ReviewRepository()
    app._auth = lambda environ: User(
        "user-a", "org-a", "admin@example.com", "hash", "ADMIN"
    )

    status, data = call(app, "GET", "/v1/reviews/persisted-review")

    assert status == "200 OK"
    assert data["review"]["review_id"] == "persisted-review"
    assert data["review"]["published_at"] == "2026-09-23T10:30:00+00:00"


def test_case_creation_accepts_a_review_that_only_exists_in_persistent_storage():
    app = ReviewDefenseAPI()
    app.repository = ReviewRepository()
    app._auth = lambda environ: User(
        "user-a", "org-a", "admin@example.com", "hash", "ADMIN"
    )

    body = json.dumps({"review_id": "persisted-review"}).encode()
    env = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/v1/cases",
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        "HTTP_IDEMPOTENCY_KEY": "case-create-1",
    }
    out = {}

    def start_response(status, headers):
        out["status"] = status

    payload = b"".join(app(env, start_response))
    data = json.loads(payload)

    assert out["status"] == "201 Created"
    assert data["case"]["review_id"] == "persisted-review"

class CaseRepository(ReviewRepository):
    def list_cases(self, organization_id):
        assert organization_id == "org-a"
        return [[
            "case-persisted", "org-a", "persisted-review", "ANALYZING",
            None, None, datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc),
            datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc),
        ]]

    def get_case_persistent(self, organization_id, case_id):
        if organization_id == "org-a" and case_id == "case-persisted":
            return self.list_cases(organization_id)[0]
        return None


def test_get_cases_hydrates_persistent_cases_into_api_store():
    app = ReviewDefenseAPI()
    app.repository = CaseRepository()
    app._auth = lambda environ: User(
        "user-a", "org-a", "admin@example.com", "hash", "ADMIN"
    )

    status, data = call(app, "GET", "/v1/cases")

    assert status == "200 OK"
    assert data["count"] == 1
    assert data["items"][0]["case_id"] == "case-persisted"
    assert data["items"][0]["status"] == "ANALYZING"
    assert ("org-a", "case-persisted") in app.store.cases


def test_get_persistent_case_hydrates_its_persistent_review():
    app = ReviewDefenseAPI()
    app.repository = CaseRepository()
    app._auth = lambda environ: User(
        "user-a", "org-a", "admin@example.com", "hash", "ADMIN"
    )

    status, data = call(app, "GET", "/v1/cases/case-persisted")

    assert status == "200 OK"
    assert data["case"]["case_id"] == "case-persisted"
    assert data["case"]["review_id"] == "persisted-review"
    assert data["review"]["review_id"] == "persisted-review"
