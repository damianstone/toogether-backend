"""
    Gets methods return querysets
"""

from django.db.models import Q
from api import models


def get_receiver(current_profile, conversation):
    receiver = conversation.participants.exclude(id=current_profile.id)
    return receiver[0]


def get_conversation_between(p1, p2):
    conversation = models.Conversation.objects.filter(participants=p1).filter(
        participants=p2
    )
    if conversation.exists():
        return conversation.first()
    else:
        return None


def get_group_between(p1,p2):
    group = models.Group.objects.filter(members=p1).filter(members=p2)
    if group.exists():
          return group.first()
    else:
        return None

def get_last_message(conversation):
    messages = models.Message.objects.filter(conversation=conversation).order_by(
        "-sent_at"
    )
    if messages.exists():
        return messages.first()
    else:
        return None

    