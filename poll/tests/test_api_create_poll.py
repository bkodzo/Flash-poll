import json
import pytest
from poll.models import Poll

CREATE_URL = "/api/polls/"

@pytest.mark.django_db
def test_create_poll_happy_path(client):
    payload = {"question": "Best Ghanaian Meal", "choices": ["Banku", "Jollof", "Fufu"]}
    resp = client.post(CREATE_URL, data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    slug = resp.json()["slug"]
    p = Poll.objects.get(slug=slug)
    assert p.choices.count() == 3

@pytest.mark.django_db
def test_create_poll_requires_nonempty_choices(client):
    resp = client.post(CREATE_URL, data=json.dumps({"question": "X", "choices": []}),
                       content_type="application/json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_create_poll_rejects_bad_payload(client):
    # missing choices
    resp = client.post(CREATE_URL, data=json.dumps({"question": "X"}), content_type="application/json")
    assert resp.status_code == 400
    # wrong type for choices
    resp = client.post(CREATE_URL, data=json.dumps({"question": "X", "choices": "A,B"}),
                       content_type="application/json")
    assert resp.status_code == 400

@pytest.mark.django_db
def test_create_poll_is_atomic_on_choice_error(client, settings):
    """If one choice is invalid (e.g., too long), nothing should be created."""
    too_long = "x" * 999  # > Choice.text max_length=120
    payload = {"question": "Atomicity", "choices": ["ok", too_long, "ok2"]}
    resp = client.post(CREATE_URL, data=json.dumps(payload), content_type="application/json")
    # want this to be a 400 (client error), not a 500, and create zero rows.
    assert resp.status_code in (400, 422)
    assert not Poll.objects.filter(question="Atomicity").exists()

def test_create_poll_method_not_allowed(client):
    resp = client.get(CREATE_URL)
    assert resp.status_code == 405
