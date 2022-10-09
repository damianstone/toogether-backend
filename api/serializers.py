from cProfile import Profile
from dataclasses import fields
from rest_framework import serializers
from api import models
from rest_framework_simplejwt.tokens import RefreshToken


class ChoicesField(serializers.Field):
    def __init__(self, choices, **kwargs):
        self._choices = choices
        super(ChoicesField, self).__init__(**kwargs)

    def to_representation(self, obj):
        if obj in self._choices:
            return self._choices[obj]
        return obj  # TODO: return an error

    def to_internal_value(self, data):
        if data in self._choices:
            return getattr(self._choices, data)
        raise serializers.ValidationError(["choice not valid"])


# -------------------------- MODELS SERIALIZERS ----------------------------


class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        required=True, allow_null=False, max_length=None, use_url=True
    )

    class Meta:
        model = models.Photo
        fields = ["id", "image", "profile"]


# TODO: make this serializer just for retrieve (with more data)
class ProfileSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    # transform the gender and show me into text "Male"
    gender = serializers.CharField(
        source="get_gender_display", required=True, allow_null=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display", required=True, allow_null=False
    )

    photos = PhotoSerializer(source="photo_set", many=True, read_only=True)

    class Meta:
        model = models.Profile
        exclude = ["user_permissions", "groups", "password"]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


# -------------------------- SWIPE SERIALIZERS -----------------------------


class SwipeProfileSerializer(serializers.ModelSerializer):
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
            "firstname",
            "lastname",
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
        ]


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
    owner = SwipeProfileSerializer(read_only=True, many=False)
    members = serializers.SerializerMethodField()
    gender = ChoicesField(
        choices=models.Group.GENDER_CHOICES,
        required=False,
        allow_null=False,
    )

    class Meta:
        model = models.Group
        fields = "__all__"

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


# -------------------------- BLOCKED PROFILES SERIALIZERS --------------------------------


class BlockedProfilesSerializer(serializers.ModelSerializer):
    blocked_profiles = SwipeProfileSerializer(read_only=True, many=True)

    class Meta:
        model = models.Profile
        fields = ["blocked_profiles"]


class MatchSerializer(serializers.ModelSerializer):
    profiles = SwipeProfileSerializer(read_only=True, many=True)

    class Meta:
        model = models.Match
        fields = ["id", "profiles"]


# -------------------------- DATA ACTIONS SERIALIZERS -----------------------------


# serializer that gonna be stored in the local storage
class CreateProfileSerializer(serializers.Serializer):
    firstname = serializers.CharField(required=True, allow_null=False)
    lastname = serializers.CharField(required=True, allow_null=False)
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
