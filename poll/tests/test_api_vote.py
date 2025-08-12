import json
import pytest
from django.db.models import F
from poll.models import Choice

VOTE_URL = "/api/vote/"

@pytest.mark.django_db
def test_vote_increments_count(client, poll_with_choices):
    p, choices = poll_with_choices
    c = choices[0]
    # vote twice
    for _ in range(2):
        resp = client.post(VOTE_URL, data=json.dumps({"choice_id": c.id}),
                           content_type="application/json")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
    # read from DB
    c.refresh_from_db()
    assert c.votes == 2

@pytest.mark.django_db
def test_vote_requires_valid_choice(client):
    resp = client.post(VOTE_URL, data=json.dumps({"choice_id": 999999}),
                       content_type="application/json")
    assert resp.status_code == 400

def test_vote_method_not_allowed(client):
    assert client.get(VOTE_URL).status_code == 405
