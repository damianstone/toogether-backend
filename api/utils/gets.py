"""
    Gets methods return querysets
"""

from django.db.models import Q
from api import models, serializers


def get_conversation_between(p1, p2):
    conversation = models.Conversation.objects.filter(participants=p1).filter(
        participants=p2
    )
    if conversation.exists():
        return conversation.first()
    else:
        return None
