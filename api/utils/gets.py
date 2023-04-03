"""
    Gets methods return querysets
"""

from django.db.models import Q
from api import models

# * -------------------------- CONVERSATIONS ----------------------------- 

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

def get_mygroup_last_message(group):
    messages = models.MyGroupMessage.objects.filter(group=group).order_by(
        "-sent_at"
    )
    if messages.exists():
        return messages.first()
    else:
        return None
    
# * -------------------------- MATCH -----------------------------    
    
def get_match(p1, p2):
    current_matches = models.Match.objects.filter(
        Q(profile1=p1) | Q(profile2=p2)
    )

    liked_matches = models.Match.objects.filter(
        Q(profile1=p2) | Q(profile2=p1)
    )

    if current_matches.filter(id__in=liked_matches).exists():
        match = current_matches.filter(id__in=liked_matches)
        return match[0]

    return False