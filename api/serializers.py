from rest_framework import serializers
from api import models
from rest_framework_simplejwt.tokens import RefreshToken

# -------------------------- MODELS SERIALIZERS -----------------------------

class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        required=True, allow_null=False, max_length=None, use_url=True
    )

    class Meta:
        model = models.Photo
        fields = ["id", "image", "profile"]


class ProfileSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    gender = serializers.CharField(
        source="get_gender_display", required=True, allow_null=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display", required=True, allow_null=False
    )

    photos = PhotoSerializer(
        source="photo_set", many=True, read_only=True
    )  # nested serializer

    class Meta:
        model = models.Profile
        fields = [
            "id",
            "email",
            "firstname",
            "lastname",
            "token",
            "birthdate",
            "age",
            "gender",
            "show_me",
            "nationality",
            "city",
            "university",
            "description",
            "created_at",
            "has_account",
            "photos",
        ]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class BlockedProfilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = ["blocked_profiles"]


class UserSerializer(ProfileSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Profile
        fields = [
            "id",
            "firstname",
            "email",
            "token",
            "created_at",
            "is_superuser",
            "has_account",
        ]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)

class SwipeProfileSerializer:
    photos = PhotoSerializer(
        source="photo_set", many=True, read_only=True
    )  # nested serializer

    class Meta:
        model = models.Profile
        fields = [
            "id",
            "email",
            "firstname",
            "lastname",
            "birthdate",
            "age",
            "gender",
            "university",
            "description",
            "photos",
        ]


# -------------------------- DATA ACTIONS SERIALIZERS -----------------------------


# serializer that gonna be stored in the local storage
class CreateProfileSerializer(serializers.Serializer):
    firstname = serializers.CharField(required=True, allow_null=False)
    lastname = serializers.CharField(required=True, allow_null=False)
    birthdate = serializers.DateField(required=True, allow_null=False)
    university = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    gender = serializers.CharField(
        source="get_gender_display", required=True, allow_null=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display", required=True, allow_null=False
    )


class UpdateProfileSerializer(serializers.Serializer):
    nationality = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    university = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    gender = serializers.CharField(
        source="get_gender_display", required=False, allow_null=False, allow_blank=False
    )
    show_me = serializers.CharField(
        source="get_show_me_display",
        required=False,
        allow_null=False,
        allow_blank=False,
    )
