from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from api.models import Profile, Conversation
from pathlib import Path

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
def get_profile(profile_id):
    # if its not a valid UUID then return an AnonymousUser
    try:
        return Profile.objects.get(pk=profile_id)
    except (ValidationError, Profile.DoesNotExist):
        return AnonymousUser()


@database_sync_to_async
def get_conversation(id):
    try:
        return Conversation.objects.get(pk=id)
    except ObjectDoesNotExist:
        return False


@database_sync_to_async
def check_conversation(conversation_id, profile_id):
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except ObjectDoesNotExist:
        return False

    # check if the profile_id is in the participants many to many field
    if conversation.participants.filter(pk=profile_id).exists():
        return True

    return False


class QueryAuthMiddleware:
    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).

        # get the match id from the url
        path = Path(scope["path"])
        conversation_id = path.parts[-1]

        # check if the scope["profile"] is already populated
        if "profile" not in scope:

            # get query params
            query_string = urllib.parse.parse_qs(scope["query_string"].decode("utf-8"))
            profile_id = query_string.get("profile_id", [None])[0]

            # create the scope
            scope["profile"] = await get_profile(profile_id)

            scope["conversation"] = await get_conversation(conversation_id)

            scope["profile_in_conversation"] = await check_conversation(
                conversation_id, profile_id
            )

        return await self.app(scope, receive, send)
