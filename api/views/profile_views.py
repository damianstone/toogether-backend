from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers
from django.contrib.auth.hashers import make_password
from datetime import date

# simple json token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# ----------------------- USER VIEWS (LOGIN / REGISTER) --------------------------------


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = serializers.UserSerializer(self.user).data
        for key, value in serializer.items():
            data[key] = value

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([AllowAny])
def registerUser(request):
    data = request.data
    password = data["password"]
    repeated_password = data["repeated_password"]

    if password != repeated_password:
        message = {"detail": "Your password does not match"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    try:
        # create a new user data model
        user = models.Profile.objects.create(
            email=data["email"], password=make_password(data["password"])
        )
        serializer = serializers.UserSerializer(user, many=False)
        return Response(serializer.data)
    except:
        message = {"detail": "User with this email already exist"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteUser(request):
    user = request.user
    user_to_delete = models.Profile.objects.get(id=user.id)
    user_to_delete.delete()
    return Response({"detail": "User deleted successfully"})


# get the internals fields
@api_view(["GET"])
@permission_classes([IsAdminUser])
def getUsers(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.UserSerializer(profiles, many=True)
    return Response(serializer.data)


# ----------------------- PROFILES VIEWS --------------------------------


class ProfileViewSet(ModelViewSet):
    queryset = models.Profile.objects.all()
    serializer_class = serializers.ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "list":  # list all the profile just for admin users
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    # user just can retrieve their profile
    def retrieve(self, request, pk=None):
        profile = models.Profile.objects.get(pk=pk)
        if profile.id != request.user.id:
            return Response(
                {"detail": "Trying to get another profile"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(user_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path=r"actions/create-profile")
    def create_profile(self, request, pk):
        def age(birthdate):
            today = date.today()
            age = (
                today.year
                - birthdate.year
                - ((today.month, today.day) < (birthdate.month, birthdate.day))
            )
            return age

        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        if profile.id != request.user.id:
            return Response(
                {"detail": "Trying to get another profile"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        fields_serializer = serializers.CreateProfileSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        profile.firstname = fields_serializer.validated_data["firstname"]
        profile.lastname = fields_serializer.validated_data["lastname"]
        profile.birthdate = fields_serializer.validated_data["birthdate"]
        profile.university = fields_serializer.validated_data["university"]
        profile.description = fields_serializer.validated_data["description"]
        profile.gender = fields_serializer.validated_data["get_gender_display"]
        profile.show_me = fields_serializer.validated_data["get_show_me_display"]

        if age(profile.birthdate) < 18:
            return Response(
                {"detail": "You must be over 18 years old to use this app"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            profile.age = age(profile.birthdate)
            profile.has_account = True

        profile.save()
        profile_serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(profile_serializer.data)

    @action(detail=True, methods=["patch"], url_path=r"actions/update-profile")
    def update_profile(self, request, pk):
        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        if profile.id != request.user.id:
            return Response(
                {"detail": "Trying to get another profile"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        fields_serializer = serializers.UpdateProfileSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        for key, val in fields_serializer.validated_data.items():
            setattr(profile, key, val)

        profile.save()
        profile_serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(profile_serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/block-profile")
    def block_profile(self, request, pk=None):
        profile = request.user
        id = request.data["id"]
        try:
            blocked_profile = models.Profile.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        profile.blocked_profiles.add(blocked_profile)
        serializer = serializers.ProfileSerializer(blocked_profile, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/disblock-profile")
    def disblock_profile(self, request, pk=None):
        profile = request.user
        id = request.data["id"]
        try:
            blocked_profile = models.Profile.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response({"Error": "Profile does not exist"})
        profile.blocked_profiles.remove(blocked_profile)
        serializer = serializers.ProfileSerializer(blocked_profile, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path=r"actions/get-blocked-profiles")
    def get_blocked_profiles(self, request, pk=None):
        profile = models.Profile.objects.get(id=pk)
        serializer = serializers.BlockedProfilesSerializer(profile, many=False)
        return Response(serializer.data)


# ----------------------- PHOTOS VIEWS --------------------------------


class PhotoViewSet(ModelViewSet):
    serializer_class = serializers.PhotoSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        profile = request.user
        queryset = models.Photo.objects.filter(profile=profile.id).order_by(
            "created_at"
        )
        serializer = serializers.PhotoSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        photo = models.Photo.objects.get(pk=pk)
        serializer = serializers.PhotoSerializer(photo, many=False)
        return Response(serializer.data)

    def create(self, request):
        profile = request.user
        profile_photos = models.Photo.objects.filter(profile=profile.id)
        # file = request.FILES.get("image")

        fields_serializer = serializers.PhotoSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        if len(profile_photos) >= 5:
            return Response(
                {"detail": "Profile cannot have more than 5 images"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo = models.Photo.objects.create(
            profile=profile, image=fields_serializer._validated_data["image"]
        )
        serializer = serializers.PhotoSerializer(photo, many=False)
        return Response(serializer.data)

    def update(self, request, pk=None, *args, **kwargs):
        photo = models.Photo.objects.get(pk=pk)
        fields_serializer = serializers.PhotoSerializer(data=request.data, partial=True)
        fields_serializer.is_valid(raise_exception=True)
        photo.image = fields_serializer._validated_data["image"]
        photo.save()
        serializer = serializers.PhotoSerializer(photo, many=False)
        return Response(serializer.data)

    def destroy(self, request, pk):
        photo = models.Photo.objects.get(pk=pk)
        photo.delete()
        return Response({"detail": "Photo deleted"}, status=status.HTTP_200_OK)
