from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from api import models

import api.utils.gets as g
import api.utils.checks as c


class ChoicesField(serializers.Field):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ChoicesField, self).__init__(**kwargs)

    def to_representation(self, obj):
        if obj in self._choices:
            return self._choices[obj]
        return obj

    def to_internal_value(self, data):
        if data in self._choices:
            return getattr(self._choices, data)
        raise serializers.ValidationError(["choice not valid"])


# -------------------------- PROFILE SERIALIZER ----------------------------
class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        required=True, allow_null=False, max_length=None, use_url=True
    )

    class Meta:
        model = models.Photo
        fields = ["id", "image", "profile"]


class ProfileSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    refresh_token = serializers.SerializerMethodField(read_only=True)

    # transform the gender and show me into text "Male"
    gender = serializers.CharField(
        source="get_gender_display", required=True, allow_null=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display", required=True, allow_null=False
    )

    photos = PhotoSerializer(source="photo_set", many=True, read_only=True)

    is_in_group = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    total_matches = serializers.SerializerMethodField()

    class Meta:
        model = models.Profile
        exclude = [
            "user_permissions",
            "groups",
            "password",
            "last_login",
            "is_staff",
            "is_active",
            "likes",
            "blocked_profiles",
        ]

    # refresh the token everytime the user is called
    def get_token(self, profile):
        token = RefreshToken.for_user(profile)
        return str(token.access_token)

    def get_refresh_token(self, profile):
        token = RefreshToken.for_user(profile)
        return str(token)

    def get_is_in_group(self, profile):
        return profile.member_group.all().exists()

    def get_total_likes(self, profile):
        matches = matches = models.Match.objects.filter(
            Q(profile1=profile.id) | Q(profile2=profile.id)
        )
        matched_profiles = [match.profile1.id for match in matches] + [
            match.profile2.id for match in matches
        ]
        likes = profile.likes.exclude(id__in=matched_profiles)
        count = likes.count()
        return count

    def get_total_matches(self, profile):
        matches = matches = models.Match.objects.filter(
            Q(profile1=profile.id) | Q(profile2=profile.id)
        )
        count = matches.count()
        return count


# -------------------------- SWIPE SERIALIZERS -----------------------------
class SwipeProfileSerializer(serializers.ModelSerializer):
    is_in_group = serializers.SerializerMethodField()
    gender = serializers.CharField(
        source="get_gender_display", required=True, allow_null=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display", required=True, allow_null=False
    )

    photos = PhotoSerializer(source="photo_set", many=True, read_only=True)

    class Meta:
        model = models.Profile
        fields = [
            "id",
            "email",
            "is_in_group",
            "name",
            "birthdate",
            "age",
            "gender",
            "show_me",
            "nationality",
            "city",
            "university",
            "description",
            "location",
            "photos",
            "instagram",
        ]

    def get_is_in_group(self, profile):
        return profile.member_group.all().exists()


class SwipeGroupSerializer(serializers.ModelSerializer):
    owner = SwipeProfileSerializer(read_only=True, many=False)
    members = SwipeProfileSerializer(read_only=True, many=True)
    gender = serializers.CharField(
        source="get_gender_display", required=False, allow_null=False
    )

    class Meta:
        model = models.Group
        fields = ["id", "gender", "total_members", "created_at", "owner", "members"]


# -------------------------- GROUP SERIALIZERS --------------------------------
class GroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()
    owner = SwipeProfileSerializer(read_only=True, many=False)
    gender = serializers.CharField(
        source="get_gender_display", required=False, allow_null=False
    )

    class Meta:
        model = models.Group
        fields = ["id", "gender", "total_members", "share_link", "owner", "members"]

    # Exclude the owner from members
    def get_members(self, group):
        # get the group
        group = models.Group.objects.get(pk=group.id)
        # filter the members and exclude the owner
        members_without_owner = group.members.exclude(id=group.owner.id)
        # serialize the members
        serializer = SwipeProfileSerializer(instance=members_without_owner, many=True)
        return serializer.data


class GroupSerializerWithLink(GroupSerializer):
    share_link = serializers.CharField(required=True, allow_null=False)


# -------------------------- MATCHED PROFILES SERIALIZERS --------------------------------
class MatchSerializer(serializers.ModelSerializer):
    current_profile = serializers.SerializerMethodField()
    matched_data = serializers.SerializerMethodField()

    class Meta:
        model = models.Match
        fields = ["id", "current_profile", "matched_data"]

    def get_current_profile(self, match):
        request = self.context.get("request")
        current_profile = request.user

        serializer = SwipeProfileSerializer(current_profile, many=False)
        return serializer.data

    def get_matched_data(self, match):
        request = self.context.get("request")
        current_profile = request.user

        if match.profile1 == current_profile:
            matched_profile = match.profile2
        else:
            matched_profile = match.profile1

        #  check if the matched profile is in a group
        if matched_profile.member_group.all().exists():
            matched_group = matched_profile.member_group.all()[0]
            members = matched_group.members.count()
            profile_serializer = SwipeProfileSerializer(matched_profile, many=False)

            return {
                "matched_profile": profile_serializer.data,
                "is_group_match": True,
                "members_count": members,
            }

        serializer = SwipeProfileSerializer(matched_profile, many=False)
        return {
            "matched_profile": serializer.data,
            "is_group_match": False,
        }


# -------------------------- CONVERSATION SERIALIZERS --------------------------------


class ReceiverSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()
    is_in_group = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Profile
        fields = ["id", "name", "email", "photo", "is_in_group", "member_count"]

    def get_is_in_group(self, profile):
        return profile.member_group.all().exists()

    def get_photo(self, profile):
        profile_photos = models.Photo.objects.filter(profile=profile).order_by(
            "-created_at"
        )
        if profile_photos.exists():
            first_photo = profile_photos.first()
            serializer = PhotoSerializer(first_photo, many=False)
            return serializer.data
        else:
            return None

    def get_member_count(self, profile):
        if profile.member_group.all().exists():
            group = profile.member_group.all()[0]
            count_members = group.members.count()
            return count_members
        return None


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_photo = serializers.SerializerMethodField()
    sent_by_current = serializers.SerializerMethodField()
    sent_at = serializers.SerializerMethodField()

    class Meta:
        model = models.Message
        fields = [
            "id",
            "message",
            "sent_at",
            "sent_by_current",
            "sender",
            "sender_name",
            "sender_photo",
        ]

    def get_sender_name(self, message):
        return message.sender.name

    def get_sender_photo(self, message):
        sender = message.sender
        sender_photos = models.Photo.objects.filter(profile=sender).order_by(
            "-created_at"
        )
        if sender_photos.exists():
            first_photo = sender_photos.first()
            serializer = PhotoSerializer(first_photo, many=False)
            return serializer.data
        else:
            return None

    def get_sent_at(self, message):
        return message.get_sent_time()

    def get_sent_by_current(self, message):
        request = self.context.get("request")
        current_profile = request.user
        return message.sender == current_profile


class ConversationSerializer(serializers.ModelSerializer):
    receiver = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = models.Conversation
        fields = ["id", "type", "receiver", "last_message"]

    def get_receiver(self, conversation):
        request = self.context.get("request")
        current_profile = request.user
        receiver = g.get_receiver(current_profile, conversation)
        serializer = ReceiverSerializer(receiver, many=False)
        return serializer.data

    def get_last_message(self, conversation):
        request = self.context.get("request")
        has_messages = c.check_conversation_with_messages(conversation)
        if has_messages:
            last_message = g.get_last_message(conversation)
            serializer = MessageSerializer(
                last_message, many=False, context={"request": request}
            )
            return serializer.data
        return None


class MyGroupConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = models.Group
        fields = ["id", "last_message"]

    def get_last_message(self, group):
        request = self.context.get("request")
        has_messages = c.check_mygroup_messages(group)
        if has_messages:
            last_message = g.get_mygroup_last_message(group)
            serializer = MessageSerializer(
                last_message, many=False, context={"request": request}
            )
            return serializer.data
        return None


# -------------------------- DATA ACTIONS SERIALIZERS -----------------------------
class CreateProfileSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, allow_null=False)
    birthdate = serializers.DateField(required=True, allow_null=False)
    university = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    gender = ChoicesField(
        choices=models.Profile.GENDER_CHOICES,
        required=False,
        allow_null=False,
    )
    show_me = ChoicesField(
        choices=models.Profile.SHOW_ME_CHOICES,
        required=False,
        allow_null=False,
    )


class UpdateProfileSerializer(serializers.Serializer):
    instagram = serializers.CharField(required=False, allow_null=True)
    nationality = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    university = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    gender = ChoicesField(
        choices=models.Profile.GENDER_CHOICES,
        required=False,
        allow_null=False,
    )
    show_me = ChoicesField(
        choices=models.Profile.SHOW_ME_CHOICES,
        required=False,
        allow_null=False,
    )


class UpdateLocation(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class GroupSerializerWithMember(serializers.Serializer):
    member_id = serializers.CharField(required=True, allow_null=False)
