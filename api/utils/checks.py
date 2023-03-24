"""
    Checks methods just return booleans
"""

from django.db.models import Q
from api import models, serializers

import api.utils.gets as g


def check_conversation_between(p1, p2):
    conversation = models.Conversation.objects.filter(participants=p1).filter(
        participants=p2
    )
    return conversation.exists()


def check_conversation_with_messages(conversation):
    messages = models.Message.objects.filter(conversation=conversation)
    print(messages.count())
    return messages.count() >= 1


def check_profiles_with_messages(p1, p2):
    conversation = g.get_conversation_between(p1, p2)
    if conversation:
        messages = check_conversation_with_messages(conversation)
        return messages
