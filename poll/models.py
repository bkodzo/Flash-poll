from django.db import models
from django.utils.text import slugify  
from django.utils import timezone
from datetime import timedelta
import secrets

class Poll(models.Model):
    question = models.CharField(max_length=240)
    slug = models.SlugField(unique=True, editable=False, db_index=True)
    session_id = models.CharField(max_length=64, db_index=True, null=True, blank=True)
    creator_ip = models.GenericIPAddressField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now_add=True, db_index=True)
    expiry_time = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['expiry_time']),
            models.Index(fields=['is_active', 'expiry_time']),
        ]

    def save(self, *args, **kwargs):
        if not self.id:
            # create slug
            base = slugify(self.question)[:40] or "poll"
            while True:
                random = secrets.token_hex(3)
                self.slug = f"{base}-{random}"
                if not Poll.objects.filter(slug=self.slug).exists():
                    break
            
            # set expiry 24hrs afrer
            self.expiry_time = timezone.now() + timedelta(hours=24)
        
        super().save(*args, **kwargs)

    def is_owned_by_session(self, session_id):
        """Check if poll is owned by current session"""
        return self.session_id == session_id

class Choice(models.Model):
    poll = models.ForeignKey(Poll, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=120)
    votes = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['poll', 'votes']),
            models.Index(fields=['votes']),
        ]