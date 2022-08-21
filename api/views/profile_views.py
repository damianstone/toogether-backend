from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers
from django.contrib.auth.hashers import make_password
from datetime import date

# simple json token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# ----------------------- USER VIEWS --------------------------------

# TOKEN SERIALIZER


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = serializers.UserSerializer(self.user).data
        for key, value in serializer.items():
            data[key] = value

        return data


# TOKEN VIEW
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(["POST"])
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


# get the internals fields
@api_view(["GET"])
@permission_classes([IsAdminUser])
def getUsers(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.UserSerializer(profiles, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteUser(request, pk):
    userForDeletion = models.Profile.objects.get(id=pk)
    userForDeletion.delete()
    return Response("User was deleted")


# ----------------------- PROFILES VIEWS --------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def createProfile(request, pk):
    
    def age(birthdate):
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    
    user = models.Profile.objects.get(id=pk)
    fields_serializer = serializers.CreateProfileSerializer(data=request.data)
    fields_serializer.is_valid(raise_exception=True)
    
    user.firstname = fields_serializer.validated_data["firstname"]
    user.lastname = fields_serializer.validated_data["lastname"]
    user.birthdate = fields_serializer.validated_data["birthdate"]
    user.university = fields_serializer.validated_data["university"]
    user.description = fields_serializer.validated_data["description"]
    
    if age(user.birthdate) < 18:
        return Response({"detail": "You must be over 18 years old to use this app"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        user.age = age(user.birthdate)
        user.has_account = True
    
    user_serializer = serializers.ProfileSerializer(user, many=False)
    return Response(user_serializer.data)


# Get all the profile users


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def updateProfile(request, pk):
    user = models.Profile.objects.get(id=pk)
    fields_serializer = serializers.UpdateProfileSerializer(data=request.data)
    fields_serializer.is_valid(raise_exception=True)
    user.university = fields_serializer.validated_data["university"]
    user.description = fields_serializer.validated_data["description"]
    user_serializer = serializers.ProfileSerializer(user, many=False)
    return Response(user_serializer.data)


# Get all the profile users


@api_view(["GET"])
@permission_classes([IsAdminUser])
def getProfiles(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.ProfileSerializer(profiles, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getProfile(request, pk):
    profile = models.Profile.objects.get(id=pk)
    serializer = serializers.ProfileSerializer(profile, many=False)
    return Response(serializer.data)


# ----------------------- PHOTOS VIEWS --------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def addPhoto(request):
    profile = request.user
    photos = models.Photo.objects.filter(profile=profile.id)
    file = request.FILES.get("image")
    if len(photos) >= 5:
        return Response({"detail": "Profile cannot have more than 5 images"})
    else:
        photo = models.Photo.objects.create(profile=profile, image=file)
        serializer = serializers.PhotoSerializer(photo, many=False)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getProfilePhotos(request):
    profile = request.user
    photos = models.Photo.objects.filter(profile=profile.id)
    serializer = serializers.PhotoSerializer(photos, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def getPhotos(request):
    photos = models.Photo.objects.all()
    serializer = serializers.PhotoSerializer(photos, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deletePhoto(request, pk):
    photo = models.Photo.objects.get(id=pk)
    photo.delete()
    return Response("Photo deleted")


# ----------------------- BLOCKED USERS --------------------------------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def blockProfile(request):
    profile = request.user
    id = request.data["id"]
    try:
        blocked_profile = models.Profile.objects.get(id=id)
    except ObjectDoesNotExist:
        return Response({"Error": "Profile does not exist"})
    profile.blocked_profiles.add(blocked_profile)
    serializer = serializers.ProfileSerializer(blocked_profile, many=False)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def disblockProfile(request):
    profile = request.user
    id = request.data["id"]
    try:
        blocked_profile = models.Profile.objects.get(id=id)
    except ObjectDoesNotExist:
        return Response({"Error": "Profile does not exist"})
    profile.blocked_profiles.remove(blocked_profile)
    serializer = serializers.ProfileSerializer(blocked_profile, many=False)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def getBlockedProfiles(request, pk):
    profile = models.Profile.objects.get(id=pk)
    serializer = serializers.BlockedProfilesSerializer(profile, many=False)
    return Response(serializer.data)