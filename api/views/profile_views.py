from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Profile, Photo
from api.serializers import ProfileSerializer, UserSerializer, PhotoSerializer, BlockedProfileSerializer
from django.contrib.auth.hashers import make_password

# simple json token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# ----------------------- USER VIEWS --------------------------------

# TOKEN SERIALIZER


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        """
        se puede hacer de la siguinte manera (de forma manual)
            data['username'] = self.user.username
            data['email'] = self.user.email

            O se puede hacer mediante un for loop usando el serializer cn el token
        """

        serializer = UserSerializer(self.user).data
        for key, value in serializer.items():
            data[key] = value

        return data


# TOKEN VIEW
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        # create a new user data model
        user = Profile.objects.create(
            email=data['email'],
            password=make_password(data['password'])
        )
        serializer = UserSerializer(user, many=False)
        return Response(serializer.data)
    except:
        message = {'detail': 'User with this email already exist'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


# get the internals fields
@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    profiles = Profile.objects.all()
    serializer = UserSerializer(profiles, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteUser(request, pk):
    userForDeletion = Profile.objects.get(id=pk)
    userForDeletion.delete()
    return Response('User was deleted')


# ----------------------- PROFILES VIEWS --------------------------------

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def createProfile(request):
    user = request.user
    serializer = ProfileSerializer(user, many=False)

    data = request.data
    # {'firstname': ['DAMIAN'], 'lastname': ['STONEEE']}
    print("THIS IS DATA ---> ", data)

    if data.get('firstname'):  # when the value not exit return None
        user.firstname = data['firstname']
    else:
        return Response({"detail": "problem with firstname"}, status=status.HTTP_400_BAD_REQUEST)
    if data.get('lastname'):
        user.lastname = data['lastname']
    else:
        return Response({"detail": "problem with lastname"}, status=status.HTTP_400_BAD_REQUEST)

    user.save()

    return Response(serializer.data)

# Get all the profile users


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateProfile(request):
    profile = request.user
    serializer = ProfileSerializer(profile, many=False)
    data = request.data
    profile.university = data["university"]
    profile.description = data["description"]
    profile.save()
    return Response(serializer.data)


# Get all the profile users


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getProfiles(request):
    profiles = Profile.objects.all()
    serializer = ProfileSerializer(profiles, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProfile(request, pk):
    profile = Profile.objects.get(id=pk)
    serializer = ProfileSerializer(profile, many=False)
    return Response(serializer.data)


# ----------------------- PHOTOS VIEWS --------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addPhoto(request):
    profile = request.user
    photos = Photo.objects.filter(profile=profile.id)
    file = request.FILES.get('image')
    if len(photos) >= 5:
        return Response({"detail": "Profile cannot have more than 5 images"})
    else:
        photo = Photo.objects.create(
            profile=profile,
            image=file
        )
        serializer = PhotoSerializer(photo, many=False)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getProfilePhotos(request):
    profile = request.user
    photos = Photo.objects.filter(profile=profile.id)
    serializer = PhotoSerializer(photos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getPhotos(request):
    photos = Photo.objects.all()
    serializer = PhotoSerializer(photos, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deletePhoto(request, pk):
    photo = Photo.objects.get(id=pk)
    photo.delete()
    return Response('Photo deleted')


# ----------------------- BLOCKED USERS --------------------------------

# get all blocked user - return the blocked user
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def blockProfile(request):
    profile = request.user
    data = request.data
    blocked_profile_id = data["blocked_profile_id"]
    blocked_profile = Profile.objects.get(id=blocked_profile_id)
    print("BLOCKED PROFILE --------->", blocked_profile)
    if not blocked_profile:
        return Response({"detail": "USER NOT FOUND"})
    else:
        profile.blocked_profiles.add(blocked_profile)
        serializer = ProfileSerializer(blocked_profile, many=False)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])   # =>>>>> NOT WORKING
def getBlockedProfiles(request):
    profile = request.user
    blocked_profiles = Profile.blockedProfiles.all()
    print("BLOCKED PROFILES ------>", blocked_profiles)
    serializer = BlockedProfileSerializer(profile, many=True)
    return Response(serializer.data)

# get all blocked user

@api_view(['PUT'])
def cancelBlock(request, pk):
    return

# get all blocked user


@api_view(['GET'])
def getBlockedProfiles(request, pk):
    return

# get all blocked user


@api_view(['GET'])
def getBlockedProfile(request, pk):
    return


# ----------------------- LIKES VIEWS --------------------------------

# get all the likes

@api_view(['GET'])
def getLikes(request, pk):
    return
