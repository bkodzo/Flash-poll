from django.db import models
from django.utils.text import slugify  
from django.utils import timezone
from datetime import timedelta
import secrets
from django.utils.text import slugify

class Poll(models.Model):
    question = models.CharField(max_length=240)
    slug = models.SlugField(unique=True, editable=False)
    time_created = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.id:
            base = slugify(self.question)[:40] or "poll"
            while True:
                random = secrets.token_hex(3)
                self.slug= F"{base}-{random}"
                if not Poll.objects.filter(slug=self.slug).exists():
                    break
            self.expiry_time = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

class Choice(models.Model):
    poll = models.ForeignKey(Poll,related_name="choices",
                             on_delete=models.CASCADE)
    text = models.CharField(max_length=120)
    votes = models.PositiveIntegerField(default=0)






