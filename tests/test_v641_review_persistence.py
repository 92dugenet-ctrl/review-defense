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
