from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers

# * list - deployment and local
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_profiles(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.ProfileSerializer(profiles, many=True)
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )


# * create 200 fake profiles - just local
"""
needs
firstname: any british name
lastname: any british lastname
instagram: random instagram username generated with the name and lastname of the fake profile
birthdate (yyyy/mm/dd): random age between the age of the current user and 5 year less or more
gender: opposite of the admin (current user)
show: everyone 
university: any random university in the UK

"""


@api_view(["POST"])
@permission_classes([IsAdminUser])
def generated_profiles(request):
    current_user = request.user
    print(current_user.gender, current_user.show_me)
    return Response({"detail": "success"})


# * delete all the fake profiles
