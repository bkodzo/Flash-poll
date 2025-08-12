import re
import pytest
from poll.models import Poll

@pytest.mark.django_db
def test_poll_slug_is_unique_and_readable():
    p1= Poll.objects.create(question="Best Ghanaian Meal")
    p2= Poll.objects.create(question="Best Ghanaian Meal")

    assert p1.slug != p2.slug
    assert p1.slug.startswith("best-ghanaian-meal")
    assert p2.slug.startswith("best-ghanaian-meal")

    #suffix pattern
    assert re.match(r"^best-ghanaian-meal(-[0-9a-f]{6})?$", p1.slug)

