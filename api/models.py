import uuid
import shortuuid
from django.utils import timezone
from datetime import timedelta
from django.contrib.gis.db import models
from model_utils import Choices
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import Q
from api.utils.generate import generate_group_code

# from background_task import background
from .managers import CustomUserManager

import api.utils.gets as g


class Profile(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = Choices(
        ("M", "Male"),
        ("W", "Female"),
        ("X", "Non-binary"),
    )

    SHOW_ME_CHOICES = Choices(
        ("M", "Men"),
        ("W", "Women"),
        ("X", "Everyone"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, null=True)
    password = models.CharField(max_length=200)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    has_account = models.BooleanField(default=False)
    is_in_group = models.BooleanField(default=False)

    location = models.PointField(srid=4326, blank=True, null=True)

    birthdate = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True)
    nationality = models.TextField(max_length=20, null=True)
    city = models.TextField(max_length=15, null=True)
    university = models.TextField(max_length=40, null=True)
    description = models.TextField(max_length=500, null=True)

    instagram = models.TextField(max_length=15, null=True)

    gender = models.CharField(
        choices=GENDER_CHOICES,
        default=GENDER_CHOICES.M,
        max_length=1,
        null=False,
        blank=False,
    )
    show_me = models.CharField(
        choices=SHOW_ME_CHOICES,
        default=SHOW_ME_CHOICES.W,
        max_length=1,
        null=False,
        blank=False,
    )

    blocked_profiles = models.ManyToManyField(
        "self", symmetrical=False, related_name="blocked_by", blank=True
    )

    # many to many of people that like the current profile
    likes = models.ManyToManyField(
        "self", symmetrical=False, related_name="liked_by", blank=True
    )

    USERNAME_FIELD = "email"
    # requred for creating user
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    # profile methods

    def block_profile(self, blocked_profile):
        # Remove likes between
        self.likes.remove(blocked_profile)
        blocked_profile.likes.remove(self)

        # Check for existing match between profiles and delete it
        match_qs = Match.objects.filter(
            Q(profile1=self, profile2=blocked_profile)
            | Q(profile1=blocked_profile, profile2=self)
        )
        if match_qs.exists():
            match_qs.delete()

        # check is there is any conversation between and delete it
        conversation = g.get_conversation_between(self, blocked_profile)
        if conversation:
            conversation.delete()

        #  check if the user is in a group with the block profile
        group = g.get_group_between(self, blocked_profile)
        
        if group:
            if group.owner == self:
                group.members.remove(blocked_profile)
            else:
                group.members.remove(self)
            group.save()
                
        self.blocked_profiles.add(blocked_profile)
        
    def delete(self):
        conversations = Conversation.objects.filter(participants=self)
        
        if conversations.count() >= 1:
            for conv in conversations:
                conv.delete()
                
        super().delete()
        
    

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(Profile, default=None, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def delete(self):
        self.image.delete(save=False)
        super().delete()


class VerificationCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.OneToOneField(
        Profile, related_name="verification_code", on_delete=models.CASCADE
    )
    email = models.EmailField(null=False, blank=False)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(minutes=15))


class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile1 = models.ForeignKey(
        Profile, related_name="profile1_matches", default=None, on_delete=models.CASCADE
    )
    profile2 = models.ForeignKey(
        Profile, related_name="profile2_matches", default=None, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)

    # @background(schedule=60*60-24)
    # def delete_old_matches(self):
    #     """
    #     Delete matches older than 14 days
    #     """
    #     NUMBER_OF_DAYS = 14

    #     try:
    #         old_matches = Match.object.all().filter(
    #             created__gte=datetime.now()-60*60*24*NUMBER_OF_DAYS
    #         )
    #         old_matches.delete()
    #         print(f"Deleted {len(old_matches)} old matches")
    #     except Exception as e:
    #         print(f"Error deleting old matches: {e}")


class Group(models.Model):
    GENDER_CHOICES = Choices(
        ("M", "Male"),
        ("W", "Female"),
        ("X", "Non-binary"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        Profile, default=None, on_delete=models.CASCADE, related_name="owner_profile"
    )
    gender = models.CharField(
        choices=GENDER_CHOICES,
        default=GENDER_CHOICES.M,
        max_length=1,
        null=False,
        blank=False,
    )
    age = models.PositiveIntegerField(null=True)
    total_members = models.PositiveIntegerField(null=True)
    share_link = models.CharField(max_length=100, unique=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    members = models.ManyToManyField(Profile, blank=True, related_name="member_group")

    matches = models.ManyToManyField(Match, blank=True, related_name="matches")
    likes = models.ManyToManyField(Profile, blank=True, related_name="group_likes")

    def save(self, *args, **kwargs):
        # set the link when the group is created
        if not self.share_link:
            self.share_link = f"join.my.group/{generate_group_code()}"

        # get the age of the group
        if not self.age:
            self.age = self.owner.age

        # get the gender of the group
        self.gender = self.owner.gender

        # count the members
        self.total_members = self.members.count()

        super().save(*args, **kwargs)


class MyGroupMessage(models.Model):
    """
    The group itself works as a chat_room and this model as its message
    The group does not require another separate model for the conversation, since our
    application only allows users to be in one group at a time
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, default=None, on_delete=models.CASCADE)
    sender = models.ForeignKey(Profile, default=None, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)

    def get_sent_time(self):
        return self.sent_at.strftime("%I:%M %p")


class Conversation(models.Model):
    """
    This model acts as the chat_room between the users belonging to a match
    The model is separated from the match
    For now the application only supports conversations type 1-1 (private)
    """

    TYPES = Choices(
        ("PRIVATE", "private"),
        ("GROUP", "group"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(Profile, related_name="conversations")
    created_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(
        choices=TYPES,
        default=TYPES.PRIVATE,
        max_length=10,
        null=True,
        blank=True,
    )
    
    def delete(self):
        # delete match and remove like relationship
        participants = self.participants.all()
        match = g.get_match(participants[0], participants[1])
        if match:
            match.delete()
            
        super().delete()


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation, default=None, on_delete=models.CASCADE
    )
    sender = models.ForeignKey(Profile, default=None, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(default=timezone.now)

    def get_sent_time(self):
        return self.sent_at.strftime("%I:%M %p")
