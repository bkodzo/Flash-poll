from django.shortcuts import render
import json 
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError, DataError

from .models import Poll, Choice

@csrf_exempt
@require_POST
def create_poll(request):
    try:
        data = json.loads(request.body)
        question = data["question"]
        choices  = data["choices"]
        # Basic validation
        if not question or not isinstance(choices, list) or not choices:
            return HttpResponseBadRequest("Invalid payload")
        # Validate each choice early
        for c in choices:
            if not isinstance(c, str) or not c.strip() or len(c) > 120:
                return HttpResponseBadRequest("Invalid choice value")
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("Invalid payload")

    try:
        with transaction.atomic():
            poll = Poll.objects.create(question=question)
            Choice.objects.bulk_create([Choice(poll=poll, text=c.strip()) for c in choices])
    except (IntegrityError, DataError):
        return HttpResponseBadRequest("Could not create poll")

    return JsonResponse({"slug": poll.slug}, status=201)

def poll_page(request, slug):
    poll = get_object_or_404(Poll, slug=slug)

    choices = poll.choices.order_by("id")
    return render(
        request, 
        "poll/poll_page.html",
        {"poll": poll, "choices": choices},
    )

@csrf_exempt
@require_POST
def cast_vote(request):
    try: 
        data = json.loads(request.body)
        cid = int(data["choice_id"])
    except(ValueError, KeyError,TypeError):
        return HttpResponseBadRequest("BAd Data")
    
    try:
        Choice.objects.filter(id=cid).update(votes=F("votes")+ 1)
        choice = Choice.objects.get(id=cid)
    except Choice.DoesNotExist:
        return HttpResponseBadRequest("Choice Not FOund")
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"poll_{choice.poll.slug}",
        {
            "type": "vote.update",
            "choice": choice.id,
            "votes": choice.votes,
        }
    )

    return JsonResponse({"ok":True, "choice_id":cid, "votes": choice.votes})









