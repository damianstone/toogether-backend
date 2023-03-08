from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers


# * list all the matches
# * add fake likes
# * unlike all
# * remove fake likes
# * add fake matches


# * List matches
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_matches(request):
    matches = models.Match.objects.all()
    serializer = serializers.MatchSerializer(matches, many=True)
    return Response(
        {"count": matches.count(), "results": serializer.data},
        status=status.HTTP_200_OK,
    )

# * Add fake likes
@api_view(["POST"])
@permission_classes([IsAdminUser])
def list_matches(request):
    matches = models.Match.objects.all()
    serializer = serializers.MatchSerializer(matches, many=True)
    return Response(
        {"count": matches.count(), "results": serializer.data},
        status=status.HTTP_200_OK,
    )
