import re
import html
from django.utils.html import strip_tags
import secrets
from django.utils.html import strip_tags
from django.core.cache import cache

def sanitize_text(text, max_length=120):
    """XSS attack prevention"""

    if not isinstance(text, str):
        return ""
    
    text = strip_tags(text) #remove html tags
    text = html.unescape(text) #decode html entities
    text = re.sub(r'[<>"\']', '', text) #remove special character
    text = text.strip() #remove whitespace

    if max_length and len(text) > max_length:
        text = text[:max_length] #limit text length to the max lenght


    
    return text

   
def validate_question(question):
    """Validate question content"""

    if not question:
        return False, "Question is required"
    
    if len(question) > 240:
        return False, "Question too long max = 240 characters"
    
    harmful_patterns = [
        r'<script',
        r'javascript:',
        r'on\w+\s*=',
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, question, re.IGNORECASE):
            return False, "Question contains invalid content"
    
    return True, ""

def validate_choices(choices):
    """Validate choices content"""

    if not isinstance(choices, list):
        return False, "Choices must be a list"
    
    if len(choices) < 2:
        return False, "At least 2 choice required"
    
    if len(choices) > 10:
        return False, "Maximum 10 choices allowed"
    
    for i, choice in enumerate(choices):
        if not isinstance(choice, str):
            return False, f"Choice {i+1} must be a string"
        
        if not choice.strip():
            return False, f"Choice {i+1} cannot be empty"
        
        if len(choice.strip()) > 120:
            return False, f"Choice {i + 1} too long (max 120 characters)"
    
    return True, ""

def get_client_ip(request):
    """gets client ip from request"""

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
    
def generate_session_id():
    """session id generator"""
    return secrets.token_urlsafe(32)


def rate_limit_poll(ip_address):
    """rate limit poll creation"""
    key = f"poll_creation_{ip_address}"
    current_count = cache.get(key,0)

    #allow x polls per hour
    if current_count >= 10:
        return False, "Too many polls created. Please try again later."
    
    cache.set(key, current_count + 1,3600)
    return True, "Poll creation allowed"

def validate_poll_content(question, choices):
    """Validate poll content"""
    if len(question.strip()) < 5:
        return False, "Question too short"
    
    if len(question.strip()) > 500:
        return False, "Question too long"
    
    # Check for repeated characters (spam indicator)
    if any(char * 5 in question for char in 'abcdefghijklmnopqrstuvwxyz'):
        return False, "Question contains suspicious patterns"
    
    # Check choices for spam
    for choice in choices:
        if len(choice.strip()) < 1:
            return False, "Choices cannot be empty"
        if len(choice.strip()) > 200:
            return False, "Choice too long"
    
    return True, "Content valid"


    
        
    


