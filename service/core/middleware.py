from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from  django.core.exceptions import ValidationError
from api.models import Profile

import urllib.parse


# ----------------- CSRF middleware --------------------------
class DisableCSRFMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        setattr(request, "_dont_enforce_csrf_checks", True)
        response = self.get_response(request)
        return response


# ----------------- WebSocket auth middleware --------------------------

@database_sync_to_async
def get_user(profile_id):
    # if its not a valid UUID then return an AnonymousUser
    try:
        return Profile.objects.get(pk=profile_id)
    except (ValidationError, Profile.DoesNotExist):
        return AnonymousUser()

class QueryAuthMiddleware:
    
    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).
        
        # get the profile ID from the query params
        query_string = urllib.parse.parse_qs(scope["query_string"].decode("utf-8"))
        profile_id = query_string.get("profile_id", [None])[0]
        
        # create the scope profile and assing it the current profile 
        scope['profile'] = await get_user(profile_id)

        return await self.app(scope, receive, send)