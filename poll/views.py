from django.shortcuts import render
import json 
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError, DataError
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.utils import timezone
from datetime import timedelta
import secrets
from .utils import (
    sanitize_text, validate_question, validate_choices, 
    get_client_ip, generate_session_id, rate_limit_poll,
    validate_poll_content
)
from .models import Poll, Choice



logger = logging.getLogger(__name__)




def generate_admin_token():
    # Generate cryptographically secure token
    token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits
    return token

# Example: "dK9xL2mN8pQ4rS7tU1vW5yZ9aB3cE6fG0hI4jK7lM"


def rate_limit_poll_creation(ip_address):
    key = f"poll_creation_{ip_address}"
    current_count = cache.get(key, 0)
    
    if current_count >= 10:  # Max 10 polls per hour
        return False, "Too many polls created"
    
    cache.set(key, current_count + 1, 3600)  # 1 hour
    return True, "Poll creation allowed"


def validate_poll_content(question, choices):
    # Check for inappropriate content
    inappropriate_words = ['spam', 'inappropriate', 'bad']  # example wrds
    
    for word in inappropriate_words:
        if word.lower() in question.lower():
            return False, "Inappropriate content detected"
    
    # Check for spam patterns
    if len(question) < 5 or len(question) > 500:
        return False, "Question length invalid"
    
    return True, "Content valid"

@csrf_exempt
@require_POST
def create_poll(request):
    logger = logging.getLogger(__name__)
    
    # Rate limiting
    client_ip = get_client_ip(request)
    can_create, message = rate_limit_poll(client_ip)
    if not can_create:
        return JsonResponse({"error": message}, status=429)
    

    try:
        data = json.loads(request.body)
        question = sanitize_text(data.get("question", ""))
        choices = [sanitize_text(choice, 120) for choice in data.get("choices", [])]
        
        
        # Basic validation
        is_valid, error_msg = validate_question(question)
        if not is_valid:
            logger.warning(f"Question Required {error_msg}")
            return JsonResponse({"error": error_msg}, status=400)
        
        #choices validation
        is_valid,error_msg = validate_choices(choices)
        if not is_valid:
            logger.warning(f"Poll creation failed: {error_msg}")
            return JsonResponse({"error": error_msg}, status=400)
        
        # Content validation
        is_valid, error_msg = validate_poll_content(question, choices)
        if not is_valid:
            logger.warning(f"Poll creation failed: {error_msg}")
            return JsonResponse({"error": error_msg}, status=400)

        
        
        ##if not question or not isinstance(choices, list) or not choices:
            #return HttpResponseBadRequest("Invalid payload")
        
        # Validate each choice early
        
        #for choice in choices:
            #if not isinstance(choice, str) or not choice.strip() or len(choice) > 120:
                #return HttpResponseBadRequest("Invalid choice value")
    
    

        
    #except (ValueError, KeyError, TypeError):
        #return HttpResponseBadRequest("Invalid payload")
    except json.JSONDecodeError as e:
        logger.error(f"Poll creation failed: Invalid JSON - {e}")
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Poll creation failed: Unexpected error - {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
    
    
    try:
        with transaction.atomic():

            #generate session id
            session_id = generate_session_id()
            

            #create poll 
            poll = Poll.objects.create(
                question=question,
                session_id=session_id,
                creator_ip=client_ip,
                is_active=True
            )
            
            #create choices
            Choice.objects.bulk_create([
                Choice(poll=poll, text=choice.strip()) for choice in choices
            ])
            
            logger.info(f"Poll created successfully: {poll.slug} by IP: {client_ip}")
            

            # Store session ownership in Django session
            if 'owned_polls' not in request.session:
                request.session['owned_polls'] = []
            
            request.session['owned_polls'].append({
                'slug': poll.slug,
                'session_id': session_id,
                'created_at': poll.time_created.isoformat()
            })
            request.session.modified = True
            
            # Prepare response
            response_data = {
                "slug": poll.slug,
                "poll_url": f"/p/{poll.slug}",
                "admin_url": f"/manage/{poll.slug}?session={session_id}",
                "expires_at": poll.expiry_time.isoformat(),
                "session_id": session_id
            }

            return JsonResponse(response_data, status=201)
            
    
    except (IntegrityError, DataError) as e:
        logger.error(f"Failed to create poll: {e}")
        return JsonResponse({"error": "Could not create poll"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error: {e} ")
        return JsonResponse({"error": "Internal server error"}, status=500)
    

        
        #return JsonResponse({"slug": poll.slug}, status=201)

def poll_page(request, slug):
    poll = get_object_or_404(
        Poll.objects.select_related().prefetch_related("choices"), 
                             slug=slug,
                             is_active=True
    )

    #check if user owns poll

    is_owner = False
    if 'owned_polls' in request.session:
        for owned_poll in request.session['owned_polls']:
            if owned_poll['slug'] == slug:
                is_owner = True
                break



    choices = poll.choices.all()
    total_votes = sum(choice.votes for choice in choices)
    
    return render(
        request, 
        "poll/poll_page.html",
        {"poll": poll, 
         "choices": choices,
         "total_votes": total_votes,
         "is_owner":is_owner},
    )

@csrf_exempt
@require_POST
def cast_vote(request):
    try: 
        data = json.loads(request.body)
        cid = int(data["choice_id"])
    except (ValueError, KeyError, TypeError) as e:
        logger.warning(f"Invalid vote data: {e}")
        return JsonResponse({"error": "Invalid choice ID provided"}, status=400)
    
    try:
        choice = Choice.objects.select_related('poll').get(id=cid)
        
        # Check if poll is active
        if not choice.poll.is_active:
            return JsonResponse({"error": "Poll is no longer active"}, status=400)
        
        # race condition prevention 
        choice.votes = F('votes') + 1
        choice.save()
        
        # refresh the choice to get updated vote count
        choice.refresh_from_db()
        
    except Choice.DoesNotExist:
        logger.warning(f"Choice with ID {cid} not found")
        return JsonResponse({"error": "Choice not found"}, status=404)
    
    # send WebSocket update
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"poll_{choice.poll.slug}",
        {
            "type": "vote.update",
            "choice": choice.id,
            "votes": choice.votes,
        }
    )

    return JsonResponse({"ok": True, "choice_id": cid, "votes": choice.votes})


def admin_poll_view(request, slug):
    """Admin view for managing poll"""
    logger.info(f"Admin view accessed for slug: {slug}")
    
    session_id = request.GET.get('session')
    logger.info(f"Session ID from URL: {session_id}")
    
    if not session_id:
        logger.warning("No session ID provided")
        return JsonResponse({"error": "Session ID required"}, status=400)
    
    try:
        poll = get_object_or_404(
            Poll.objects.select_related().prefetch_related("choices"),
            slug=slug,
            session_id=session_id,
            is_active=True
        )
        logger.info(f"Poll found: {poll.question}")
        is_owner = True
        
    except Poll.DoesNotExist:
        logger.warning(f"Poll not found with slug: {slug} and session: {session_id}")
        return JsonResponse({"error": "Access denied"}, status=403)
    
    choices = poll.choices.all()
    total_votes = sum(choice.votes for choice in choices)
    
    context = {
        'poll': poll,
        'choices': choices,
        'total_votes': total_votes,
        'is_owner': True
    }
    
    return render(request, 'poll/admin_poll.html', context)

@csrf_exempt
@require_POST
def admin_poll_delete(request, slug):
    """Delete poll (admin only)"""
    poll = get_object_or_404(Poll, slug=slug, is_active=True)
    
    # Check if user owns this poll
    is_owner = False
    if 'owned_polls' in request.session:
        for owned_poll in request.session['owned_polls']:
            if owned_poll['slug'] == slug:
                is_owner = True
                break
    
    if not is_owner:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Soft delete
    poll.is_active = False
    poll.save()
    
    # Remove from session
    if 'owned_polls' in request.session:
        request.session['owned_polls'] = [
            p for p in request.session['owned_polls'] 
            if p['slug'] != slug
        ]
        request.session.modified = True
    
    logger.info(f"Poll deleted: {poll.slug}")
    return JsonResponse({"message": "Poll deleted successfully"})



@csrf_exempt
@require_POST
def admin_poll_extend(request, slug):
    """Extend poll expiry (admin only)"""
    poll = get_object_or_404(Poll, slug=slug, is_active=True)
 

    is_owner = False
    if 'owned_polls' in request.session:
        for owned_poll in request.session['owned_polls']:
            if owned_poll['slug'] == slug:
                is_owner = True
                break

    if not is_owner:
        return JsonResponse({"error": "Access denied"}, status=403)
    
    # Extend by 24 hours
    poll.expiry_time = timezone.now() + timedelta(hours=24)
    poll.save()
    
    return JsonResponse({
        "message": "Poll extended",
        "new_expiry": poll.expiry_time.isoformat()
    })
