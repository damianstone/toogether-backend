from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from api import models, serializers
import random


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


# * Get match by id
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_match(request, pk=None):
    try:
        match = models.Match.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Object does not exist"}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = serializers.MatchSerializer(match, many=False)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# * Add fake likes to my profile
@api_view(["POST"])
@permission_classes([IsAdminUser])
def generate_likes(request):
    current_user = request.user
    # check not making this request in production
    if not settings.DEBUG:
        return Response(
            {"error": "This action cannot be performed in production"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # current user likes
    likes = current_user.likes.all()

    # profiles liked by current user
    liked_by = current_user.liked_by.all()

    # to exclude the likes that the user already have and the likes he has already gave to other profiles
    ids_to_exclude = set(
        list(likes.values_list("likes__id", flat=True))
        + list(liked_by.values_list("liked_by__id", flat=True))
    )

    # exclude here
    profiles_excluded = models.Profile.objects.all().exclude(id__in=ids_to_exclude)
    profiles = profiles_excluded.exclude(id=current_user.id)
    profiles_no_in_group = profiles.exclude(is_in_group=True)
    groups = models.Group.objects.all()

    profiles_likes = []
    for i in range(20):
        current_user.likes.add(profiles_no_in_group[i])
        profiles_likes.append(profiles_no_in_group[i])

    group_likes = []
    for i in range(10):
        member = groups[i].owner
        current_user.likes.add(member)
        group_likes.append(groups[i])

    groups_serializer = serializers.SwipeGroupSerializer(group_likes, many=True)
    profiles_serializer = serializers.SwipeProfileSerializer(profiles_likes, many=True)
    data = groups_serializer.data + profiles_serializer.data

    return Response(
        {
            "total_count": len(data),
            "group_likes": len(group_likes),
            "profile_likes": len(profiles_likes),
            "results": data,
        },
        status=status.HTTP_200_OK,
    )


# * Remove all likes from my profile
@api_view(["POST"])
@permission_classes([IsAdminUser])
def remove_all_likes(request):
    current_user = request.user
    likes = current_user.likes.all()

    for like in likes:
        current_user.likes.remove(like)

    return Response({"detail": f"{likes.count()} profiles removed from likes"})


# * Unlike all
@api_view(["POST"])
@permission_classes([IsAdminUser])
def unlike_all(request):
    current_user = request.user
    liked_by_current = current_user.liked_by.all()

    for profile in liked_by_current:
        profile.likes.remove(current_user)

    return Response({"detail": f"{liked_by_current.count()} profiles unliked"})
