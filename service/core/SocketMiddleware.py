from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from api.models import Profile, Conversation, Group
from pathlib import Path

import urllib.parse


@database_sync_to_async
def get_sender(sender_id):
    # if its not a valid UUID then return an AnonymousUser
    try:
        return Profile.objects.get(pk=sender_id)
    except (ValidationError, Profile.DoesNotExist):
        return AnonymousUser()


@database_sync_to_async
def get_conversation(id):
    try:
        return Conversation.objects.get(pk=id)
    except ObjectDoesNotExist:
        return False


@database_sync_to_async
def check_conversation(conversation_id, sender_id):
    try:
        conversation = Conversation.objects.get(pk=conversation_id)
    except ObjectDoesNotExist:
        return False

    # check if the profile_id is in the participants many to many field
    if conversation.participants.filter(pk=sender_id).exists():
        return True

    return False


@database_sync_to_async
def get_group(id):
    try:
        return Group.objects.get(pk=id)
    except ObjectDoesNotExist:
        return False


@database_sync_to_async
def check_member_in_group(group_id, sender_id):
    try:
        group = Group.objects.get(pk=group_id)
    except ObjectDoesNotExist:
        return False

    # check if the profile_id is in the participants many to many field
    if group.members.filter(pk=sender_id).exists():
        return True

    return False


class SocketAuthMiddleware:
    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):

        # get the url
        path = Path(scope["path"])
        # get the room id: the rooms id can be the conversation id or the group id
        room_id = path.parts[-1]

        # check if the scope["profile"] is already populated
        if "sender" not in scope:

            # get query params
            query_string = urllib.parse.parse_qs(scope["query_string"].decode("utf-8"))
            sender_id = query_string.get("sender_id", [None])[0]
            my_group_chat = query_string.get("my_group_chat", [None])[0]

            # create scope variables
            scope["sender"] = await get_sender(sender_id)

            if my_group_chat == "true":
                scope["my_group_chat"] = True
                scope["model"] = await get_group(room_id)
                scope["sender_in_model"] = await check_member_in_group(
                    room_id, sender_id
                )
                scope["room_id"] = room_id
                
            else:
                scope["my_group_chat"] = False
                scope["model"] = await get_conversation(room_id)
                scope["sender_in_model"] = await check_conversation(
                    room_id, sender_id
                )
                scope["room_id"] = room_id

        return await self.app(scope, receive, send)
