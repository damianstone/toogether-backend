from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from api import models, serializers
from service.core.pagination import CustomPagination
from django.contrib.auth.hashers import make_password
from datetime import date
from django.contrib.gis.geos import GEOSGeometry
from decimal import *
from django.core.mail import send_mail
import string
import random
from datetime import timedelta
from django.utils import timezone
import json


# simple json token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# ----------------------- LOGIN --------------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = serializers.ProfileSerializer(self.user).data
        for key, value in serializer.items():
            data[key] = value

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]


# ----------------------- PROFILES VIEWS --------------------------------

ALLOW_ANY = ["create", "recovery_code", "validate_code"]


class ProfileViewSet(ModelViewSet):
    queryset = models.Profile.objects.all()
    serializer_class = serializers.ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    # admin actions for this model view set
    def get_permissions(self):
        if self.action in ALLOW_ANY:
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def list(self, request):
        return Response(
            {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
        )

    # * Register
    def create(self, request):
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
            serializer = serializers.ProfileSerializer(user, many=False)
            return Response(serializer.data)
        except:
            message = {"detail": "User with this email already exist"}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        # only the current user and an admin can execute this function
        if profile.id != request.user.id and not request.user.is_superuser:
            return Response(
                {
                    "detail": "Not autherized",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        fields_serializer = serializers.UpdateProfileSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        # only the current user and an admin can execute this function
        if profile.id != request.user.id and not request.user.is_superuser:
            return Response(
                {
                    "detail": "Not autherized",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if "gender" in request.data:
            profile.gender = fields_serializer.validated_data["gender"]
        if "show_me" in request.data:
            profile.show_me = fields_serializer.validated_data["show_me"]
        if "nationality" in request.data:
            profile.nationality = fields_serializer.validated_data["nationality"]
        if "city" in request.data:
            profile.city = fields_serializer.validated_data["city"]
        if "instagram" in request.data:
            profile.instagram = fields_serializer.validated_data["instagram"]
        if "university" in request.data:
            profile.university = fields_serializer.validated_data["university"]
        if "description" in request.data:
            profile.description = fields_serializer.validated_data["description"]

        profile.save()
        profile_serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(profile_serializer.data)

    def destroy(self, request, pk=None):
        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        # only the current user and an admin can execute this function
        if profile.id != request.user.id and not request.user.is_superuser:
            return Response(
                {
                    "detail": "Not autherized",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        profile.delete()
        return Response(
            {"detail": "User deleted successfully"}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path=r"actions/create-profile")
    def create_profile(self, request):
        profile = request.user

        def age(birthdate):
            today = date.today()
            age = (
                today.year
                - birthdate.year
                - ((today.month, today.day) < (birthdate.month, birthdate.day))
            )
            return age

        fields_serializer = serializers.CreateProfileSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        profile.name = fields_serializer.validated_data["name"]
        profile.birthdate = fields_serializer.validated_data["birthdate"]
        profile.university = fields_serializer.validated_data["university"]
        profile.description = fields_serializer.validated_data["description"]
        profile.gender = fields_serializer.validated_data["gender"]
        profile.show_me = fields_serializer.validated_data["show_me"]

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

    @action(detail=False, methods=["post"], url_path=r"actions/location")
    def update_location(self, request):
        profile = request.user

        # receives lat and lon
        fields_serializer = serializers.UpdateLocation(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        lat = fields_serializer.validated_data["lat"]
        lon = fields_serializer.validated_data["lon"]

        # update the location point using the new lat and lon
        point = {"type": "Point", "coordinates": [lat, lon]}

        profile.location = GEOSGeometry(json.dumps(point), srid=4326)
        profile.save()
        serializer = serializers.ProfileSerializer(profile, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/block-profile")
    def block_profile(self, request, pk=None):
        profile = request.user
        try:
            blocked_profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        profile.blocked_profiles.add(blocked_profile)
        serializer = serializers.SwipeProfileSerializer(blocked_profile, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/disblock-profile")
    def disblock_profile(self, request, pk=None):
        profile = request.user
        try:
            blocked_profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({"Error": "Profile does not exist"})
        profile.blocked_profiles.remove(blocked_profile)
        serializer = serializers.SwipeProfileSerializer(blocked_profile, many=False)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"actions/get-blocked-profiles")
    def get_blocked_profiles(self, request):
        current_profile = request.user
        blocked_profiles = current_profile.blocked_profiles.all()
        serializer = serializers.SwipeProfileSerializer(blocked_profiles, many=True)
        return Response({"count": blocked_profiles.count(), "results": serializer.data})

    @action(detail=False, methods=["post"], url_path=r"actions/recovery-code")
    def recovery_code(self, request):
        data = request.data
        # * 1 - comprobar que el mail existe en la base de datos usando el email
        # * 2 - si no existe devolver una respuesta con un error 
        # * 3 - si el mail existe enviar un codigo por mail para restablecer la contraseña 
        # * 4 - el codigo debe expirar despues de 5 minutos 
        Profile_email =  models.Profile.objects.filter(email=data["email"])
        VerificationCode_email = models.VerificationCode.objects.filter(email=data["email"])
        
        if Profile_email.exists():
            letters_and_digits = string.ascii_letters + string.digits
            codeGenerator = ''.join(random.choice(letters_and_digits.upper()) for i in range(6))
            
            if VerificationCode_email.exists():
                current_user = models.VerificationCode.objects.get(email=data["email"])
                current_user.code = codeGenerator
                current_user.expires_at = timezone.now() + timedelta(minutes=5)
                current_user.save()
            else:
                new_user = models.VerificationCode.objects.create(
                    email=data["email"],
                    code=codeGenerator,
                    expires_at=timezone.now() + timedelta(minutes=5))
                new_user.save()

            send_mail(
            'Reset your password',
            f'Here is your access code {codeGenerator}',
            'toogethersite@gmail.com',
            [data["email"]],
            fail_silently=False,
            )
            return Response({"message": "Your recovery email was sent succesfully"}, status=status.HTTP_200_OK)
        else: 
            return Response({"message": "email doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=["post"], url_path=r"actions/validate-code")
    def validate_code(self, request):
        
        data = request.data

        VerificationCode_code =models.VerificationCode.objects.filter(code=data["code"])

        if VerificationCode_code.exists():
            expiration = models.VerificationCode.objects.get(email=data["email"])
            user = models.Profile.objects.get(email=data["email"])

            if(timezone.now() < expiration.expires_at):
                serializer = serializers.ProfileSerializer(user, many=False)
                return Response({"user": f'{user}', "VERIFIED": True, "AccessToken": serializer.data["token"]}, status=status.HTTP_200_OK)
            else:
                    return Response({"message": "Expirated code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Invalid Code"}, status=status.HTTP_400_BAD_REQUEST) 
        # * 1 - input -> code and user_email
        # * 2 - comprobar que el codigo sea valido y que no este expirado
        # * 3 - si esta expirado o no es valido enviar diferentes respuestas (expirado / no valido)
        # * 5 - si el codigo no esta expirado y esta validado, traer el usuario usando el email
        # * 6 - autentificar al usario (devolver el auth token) y la propiedad VERIFIED: boolean
    
    @action(detail=False, methods=["post"], url_path=r"actions/reset-password")
    def reset_password(self, request):
        # este endpoint necesita authentification (token)
        current_profile = request.data 
        profile_to_change = models.Profile.objects.get(email=current_profile["email"])

        if current_profile["new_pasword"] == current_profile["repeated_new_pasword"]:
            profile_to_change.password = make_password(current_profile["new_pasword"])
            profile_to_change.save()
            return Response({"OPERATION_SUCCESS": True}, status=status.HTTP_200_OK)
        
        else:
            return Response({"OPERATION_SUCCESS": False, "message": "passwords are not equals"}, status=status.HTTP_200_OK)
        
        # * 1 - input user_mail, new_passord y repeated_new_password
        # * 2 - cambiar la contraseña del usuario y encriptarla 
        # * 3 - return OPERATION_SUCCESS: boolean
        
        pass


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
        photo.image = fields_serializer.validated_data["image"]

        photo.save()
        serializer = serializers.PhotoSerializer(photo, many=False)
        return Response(serializer.data)

    def destroy(self, request, pk):
        photo = models.Photo.objects.get(pk=pk)
        photo.delete()
        return Response({"detail": "Photo deleted"}, status=status.HTTP_200_OK)
