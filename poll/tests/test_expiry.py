import pytest
from freezegun import freeze_time
from django.utils import timezone
from poll.models import Poll
from poll.tasks import prune_expired

@pytest.mark.django_db
def test_poll_pruned_after_ttl():
    # Freeze time at a known point
    with freeze_time("2025-07-20 12:00:00"):
        p = Poll.objects.create(question="Short lived")
        expiry_time = p.expiry_time

        # Still present just before expiry
        with freeze_time(expiry_time - timezone.timedelta(seconds=1)):
            assert Poll.objects.filter(id=p.id).exists()

        # After expiry, the prune task should delete it
        with freeze_time(expiry_time + timezone.timedelta(seconds=1)):
            deleted = prune_expired()
            assert deleted >= 1
            assert not Poll.objects.filter(id=p.id).exists()
