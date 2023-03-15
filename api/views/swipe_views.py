from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.measure import D
from django.db.models import Q
from itertools import chain

from api import models, serializers
import api.handlers.matchmaking as matchmaking
import api.handlers.swipe_filters as swipefilters


class SwipeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    # * List swipe profiles cards
    def list(self, request):
        current_profile = request.user
        profiles = models.Profile.objects.all().filter(has_account=True)
        groups = models.Group.objects.all()

        # Check if the profile has an age
        if not current_profile.age:
            return Response(
                {"details": "You need an account to perform this action"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if the user has set their location
        if current_profile.location == None:
            return Response(
                {
                    "details": "You need to set your current location to perform this action"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Filter profiles and groups by distance
        profiles_by_distance = profiles.filter(
            location__distance_lt=(current_profile.location, D(km=8))
        )

        # All the groups that have at least one member within the distance
        groups_by_distance = groups.filter(members__in=profiles_by_distance).distinct()

        # Apply swipe filters
        show_profiles = swipefilters.filter_profiles(
            current_profile, profiles_by_distance
        )
        show_groups = swipefilters.filter_groups(current_profile, groups_by_distance)

        # Serialize data
        profiles_serializer = serializers.SwipeProfileSerializer(
            show_profiles, many=True
        )
        groups_serializer = serializers.SwipeGroupSerializer(show_groups, many=True)

        # Concatenate groups and profiles data
        data = groups_serializer.data + profiles_serializer.data  # type: ignore

        # Custom response
        return Response(
            {
                "distance": "8km",
                "count": len(data),
                "group_count": show_groups.count(),
                "profile_count": show_profiles.count(),
                "results": data,
            }
        )

    def retrieve(self, request, pk=None):
        profile = models.Profile.objects.get(pk=pk)
        serializer = serializers.SwipeProfileSerializer(profile, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path=r"actions/get-swipe-profile")
    def get_swipe_profile(self, request, pk=None):
        # get a profile as single or as a group
        try:
            profile = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # check if the profile is in a group
        if profile.member_group.all().exists():
            profile_group = profile.member_group.all()[0]
            group_serializer = serializers.SwipeGroupSerializer(
                profile_group, many=False
            )
            return Response(group_serializer.data)

        # if the profile is not in a group then return it as a single profile
        profile_serializer = serializers.SwipeProfileSerializer(profile, many=False)
        return Response(profile_serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/like")
    def like(self, request, pk=None):
        current_profile = request.user

        # profile to give like
        liked_profile = models.Profile.objects.get(pk=pk)

        current_is_in_group = current_profile.is_in_group
        liked_is_in_group = liked_profile.is_in_group

        # check for one to one
        if not current_is_in_group and not liked_is_in_group:
            return matchmaking.like_one_to_one(request, current_profile, liked_profile)

        # like one to group
        if not current_is_in_group and liked_is_in_group:
            liked_group = liked_profile.member_group.all()[0]
            return matchmaking.like_one_to_group(request, current_profile, liked_group)

        # like group to one
        if current_is_in_group and not liked_is_in_group:
            current_group = current_profile.member_group.all()[0]
            return matchmaking.like_group_to_one(
                request, current_profile, current_group, liked_profile
            )

        # like group to group
        if current_is_in_group and liked_is_in_group:
            current_group = current_profile.member_group.all()[0]
            liked_group = liked_profile.member_group.all()[0]
            return matchmaking.like_group_to_group(
                request, current_profile, current_group, liked_group
            )

        return Response(
            {"details": "Something went wrong when giving like"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"], url_path=r"actions/unlike")
    def unlike(self, request, pk=None):
        # unlike profile or group that I liked previously
        current_profile = request.user

        try:
            unliked_profile = models.Profile.objects.get(pk=pk)
        except:
            try:
                unliked_profile = models.Group.objects.get(pk=pk)
            except ObjectDoesNotExist:
                return Response(
                    {"Error": "Profile does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        unliked_profile.likes.remove(current_profile)
        return Response({"details": "Unliked"})

    @action(detail=True, methods=["post"], url_path=r"actions/remove-like")
    def remove_like(self, request, pk=None):
        current_profile = request.user
        try:
            profile_to_remove = models.Profile.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # if its a group then remove all members likes
        if profile_to_remove.member_group.all().exists():
            group_id = profile_to_remove.member_group.all()[0].id
            try:
                group = models.Group.objects.get(pk=group_id)
            except ObjectDoesNotExist:
                return Response(
                    {"Error": "Profile does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for member in group.members.all():
                current_profile.likes.remove(member)
        else:
            current_profile.likes.remove(profile_to_remove)

        return Response({"details": "Like removed"})

    @action(detail=False, methods=["get"], url_path=r"actions/get-likes")
    def list_likes(self, request):
        current_profile = request.user

        #  tuple of the profiles ids
        current_matches_ids = models.Match.objects.filter(
            Q(profile1=current_profile.id) | Q(profile2=current_profile.id)
        ).values_list("profile1", "profile2")

        # transform to a list of ids
        current_matches_ids = list(chain.from_iterable(current_matches_ids))

        # all the current profile likes excluding the ones in which has a match
        likes = current_profile.likes.exclude(id__in=current_matches_ids).distinct()

        # get all the likes in the current user group
        if current_profile.is_in_group:
            current_group = current_profile.member_group.all()[0]
            current_group_likes = current_group.likes.exclude(
                id__in=current_matches_ids
            ).distinct()
            likes = likes.union(current_group_likes)

        # single profile likes
        profile_likes = []

        # profiles in group likes
        group_likes = []

        for like_profile in likes:
            # check wheter the like profile in is group or not
            if like_profile.member_group.all().exists():
                group = like_profile.member_group.all()[0]
                has_match = matchmaking.check_profile_group_has_match(
                    current_profile.id, group
                )
                if group not in group_likes and not has_match:
                    group_likes.append(group)
            else:
                profile_likes.append(like_profile)

        # serialize groups and profiles
        groups_serializer = serializers.SwipeGroupSerializer(group_likes, many=True)
        profiles_serializer = serializers.SwipeProfileSerializer(
            profile_likes, many=True
        )

        # combine serializers to return group and profile models
        data = groups_serializer.data + profiles_serializer.data

        return Response(
            {"count": len(data), "results": data}, status=status.HTTP_200_OK
        )


class MatchModelViewSet(ModelViewSet):
    queryset = models.Match.objects.all()
    serializer_class = serializers.MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create" or self.action == "update":
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    # list the current profile matches
    def list(self, request):
        current_profile = request.user
        matches = models.Match.objects.filter(
            Q(profile1=current_profile.id) | Q(profile2=current_profile.id)
        )

        # Context enable the access of the current user (the user that make the request) in the serializers
        serializer = serializers.MatchSerializer(
            matches, many=True, context={"request": request}
        )
        return Response(
            {"count": matches.count(), "results": serializer.data},
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, pk=None):
        current_profile = request.user

        try:
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"Error": "Profile does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        if (
            current_profile.id == match.profile1.id
            or current_profile.id == match.profile2.id
        ):
            serializer = serializers.MatchSerializer(
                match, many=False, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
        )

    def destroy(self, request, pk=None):
        current_profile = request.user

        try:
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"details": "Match does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        matched_profile = matchmaking.get_matched_profile(current_profile, match)

        # if its a group then remove all members likes
        if matched_profile.member_group.all().exists():
            group_id = matched_profile.member_group.all()[0].id
            try:
                group = models.Group.objects.get(pk=group_id)
            except ObjectDoesNotExist:
                return Response(
                    {"Error": "Profile does not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for member in group.members.all():
                current_profile.likes.remove(member)
        else:
            current_profile.likes.remove(matched_profile)

        matched_profile.likes.remove(current_profile)
        match.delete()
        return Response({"details": "Match deleted"}, status=status.HTTP_200_OK)
