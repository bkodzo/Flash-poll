import pytest
from poll.models import Poll, Choice

@pytest.fixture
def poll_with_choices(db):
    p = Poll.objects.create(question = "API Test Poll")
    choices = Choice.objects.bulk_create([
        Choice(poll=p, text="A"),
        Choice(poll=p, text="B"),
        Choice(poll=p, text="C"),
    ])

    return p, choices