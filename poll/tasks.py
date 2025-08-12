from celery import shared_task
from django.utils import timezone
from .models import Poll

@shared_task
def prune_expired():
    qs = Poll.objects.filter(expiry_time__lte=timezone.now())
    deleted, _ = qs.delete()
    return deleted
