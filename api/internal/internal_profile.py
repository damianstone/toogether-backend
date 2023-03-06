from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_profiles(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.ProfileSerializer(profiles, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# * list
# * create fake profiles
# *
