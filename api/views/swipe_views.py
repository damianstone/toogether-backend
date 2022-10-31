from unicodedata import name
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.db.models import Q
from api import models, serializers
from datetime import date
import random


# response constants to identify the type of match in the frontend
ALREADY_MATCHED = "ALREADY_MATCHED"
NEW_MATCH = "NEW_MATCH"
SAME_MATCH = "SAME_MATCH"
LIKE = "LIKE"

# constants to identify who is the group in the match
NEITHER = "NEITHER"
BOTH = "BOTH"
LIKED = "LIKED"
CURRENT = "CURRENT"


def age_range(data, min_age, max_age):
    current = now().date()
    min_date = date(current.year - min_age, current.month, current.day)
    max_date = date(current.year - max_age, current.month, current.day)

    return data.filter(birthdate__gte=max_date, birthdate__lte=min_date)


# Profiles already filtered by distance
def filter_profiles(current_profile, profiles):
    profile_age = current_profile.age
    blocked_profiles = current_profile.blocked_profiles.all()
    show_gender = current_profile.show_me  # M, W, X -> X means Man and Woman

    # dont show profiles that are in groups
    profiles_not_in_group = profiles.filter(is_in_group=False)

    # Filter by the gender that the current user want to see
    if show_gender == "X":
        show_profiles = profiles_not_in_group
    else:
        show_profiles = profiles_not_in_group.filter(gender=show_gender)

    # Exclude the blocked profiles the user has
    show_profiles = show_profiles.exclude(id__in=blocked_profiles)

    # exclude any profile that has blocked the current user
    if current_profile.blocked_by.all().exists():
        blocked_by_profiles = current_profile.blocked_by.all()
        show_profiles = show_profiles.exclude(id__in=blocked_by_profiles)

    # Show profiles between in a range of ages
    if profile_age == 18 or profile_age == 19:
        show_profiles = age_range(show_profiles, profile_age - 1, profile_age + 6)
    else:
        show_profiles = age_range(show_profiles, profile_age - 5, profile_age + 5)

    # exclude the current user in the swipe
    show_profiles = show_profiles.exclude(id=current_profile.id)

    # filter liked profiles
    profiles_already_liked = current_profile.liked_by.filter(id__in=show_profiles)
    # exclude profiles already liked
    show_profiles = show_profiles.exclude(id__in=profiles_already_liked)

    return show_profiles


# Groups already filtered by distance
def filter_groups(current_profile, groups):
    profile_age = current_profile.age
    blocked_profiles = current_profile.blocked_profiles.all()
    show_gender = current_profile.show_me

    # filter by gender
    if show_gender == "X":
        show_groups = groups
    else:
        show_groups = groups.filter(gender=show_gender)

    # if the user in a group, don't show their group in the swipe
    if current_profile.member_group.all().exists():
        for group in groups:
            if group.members.filter(id=current_profile.id).exists():
                show_groups = show_groups.exclude(id=group.id)

    # exclude groups that has any blocked profile in their members
    for group in groups:
        for blocked_profile in blocked_profiles:
            if group.members.filter(id=blocked_profile.id).exists():
                show_groups = show_groups.exclude(id=group.id)

        # exclude any group that contains a member that has blocked the current user
        if current_profile.blocked_by.all().exists():
            for blocked_by_profile in current_profile.blocked_by.all():
                if group.members.filter(id=blocked_by_profile.id).exists():
                    show_groups = show_groups.exclude(id=group.id)

    # show groups between in a range of age
    if profile_age == 18 or profile_age == 19:
        # filter age >= number and age <= number
        show_groups = show_groups.filter(
            age__gte=profile_age - 1, age__lte=profile_age + 6
        )
    else:
        show_groups = show_groups.filter(
            age__gte=profile_age - 5, age__lte=profile_age + 5
        )

    # TODO: filter by min of 2 members
    show_groups = show_groups.filter(total_members__gte=1)

    # filter all the groups that has a like from the current profile
    groups_liked_by_current_profile = show_groups.filter(likes=current_profile.id)
    # exclude liked groups
    show_groups = show_groups.exclude(id__in=groups_liked_by_current_profile)

    return show_groups


def get_matched_profile(current_profile, match):
    if current_profile.id == match.profile1.id:
        return match.profile2
    return match.profile1


def check_two_profiles_have_match(profile1_id, profile2_id):
    current_matches = models.Match.objects.filter(
        Q(profile1=profile1_id) | Q(profile2=profile1_id)
    )

    liked_matches = models.Match.objects.filter(
        Q(profile1=profile2_id) | Q(profile2=profile2_id)
    )

    if current_matches.filter(id__in=liked_matches).exists():
        # return the match
        return True

    return False


def check_profile_group_has_match(profile_id, group):
    current_profile_matches = models.Match.objects.filter(
        Q(profile1=profile_id) | Q(profile2=profile_id)
    )

    # it is a many to many
    group_matches = group.matches.all()

    if current_profile_matches.filter(id__in=group_matches).exists():
        return True

    return False


def check_two_group_has_match(group1, group2):
    group1_matches = group1.matches.all()
    group2_matches = group2.matches.all()

    if group1_matches.filter(id__in=group2_matches).exists():
        return True

    return False


def get_match(profile1_id, profile2_id):
    current_matches = models.Match.objects.filter(
        Q(profile1=profile1_id) | Q(profile2=profile1_id)
    )

    liked_matches = models.Match.objects.filter(
        Q(profile1=profile2_id) | Q(profile2=profile2_id)
    )

    if current_matches.filter(id__in=liked_matches).exists():
        match = current_matches.filter(id__in=liked_matches)
        return match[0]

    return False


def like_one_to_one(current_profile, liked_profile):
    # like the profile
    liked_profile.likes.add(current_profile)

    # check if the current profile is already a like of the liked_profile (mutual like)
    if current_profile.likes.filter(id=liked_profile.id).exists():

        already_matched = check_two_profiles_have_match(
            current_profile.id, liked_profile.id
        )

        if already_matched:
            return Response({"details": ALREADY_MATCHED})

        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        match_serializer = serializers.MatchSerializer(match, many=False)
        return Response(
            {
                "details": NEW_MATCH,
                "group_match": NEITHER,
                "match_data": match_serializer.data,
            }
        )

    return Response({"details": LIKE})


def like_one_to_group(current_profile, liked_group):
    liked_group.likes.add(current_profile)

    # check if the current profile has already a match with the group
    already_matched = check_profile_group_has_match(current_profile.id, liked_group)
    if already_matched:
        return Response({"details": ALREADY_MATCHED})

    # check and get all the members who has given a like to the current profile
    members = []
    for member in liked_group.members.all():
        if current_profile.likes.filter(id=member.id).exists():
            members.append(member)

    # if any member has give a like to the current profile...
    if len(members) > 0:
        # make a match with a member that does not have a previous match
        for member in members:
            already_matched = check_two_profiles_have_match(
                current_profile.id, member.id
            )
            if not already_matched:
                match = models.Match.objects.create(
                    profile1=current_profile, profile2=member
                )
                match.save()
                liked_group.matches.add(match)
                liked_group.save()

                match_serializer = serializers.MatchSerializer(match, many=False)

                return Response(
                    {
                        "details": NEW_MATCH,
                        "group_match": LIKED,
                        "match_data": match_serializer.data,
                    }
                )

        # if there is no member with which it does not have a match, recycle the previous match
        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(match, many=False)
                return Response(
                    {
                        "details": SAME_MATCH,
                        "group_match": LIKED,
                        "match_data": match_serializer.data,
                    }
                )

    return Response({"details": LIKE})


def like_group_to_one(current_profile, current_group, liked_profile):
    # add the like
    liked_profile.likes.add(current_profile)

    # check if the liked profile has already a match with the group
    already_matched = check_profile_group_has_match(liked_profile.id, current_group)
    if already_matched:
        return Response({"details": ALREADY_MATCHED})

    # check if liked profile already like the group (mutual like)
    # if there is a mutal like and a match has not been found in the foor,
    # so it is because it must be the first member to like the profile
    if current_group.likes.filter(id=liked_profile.id).exists():
        # check if the current user has already a match with the liked profile
        already_match = get_match(current_profile.id, liked_profile.id)
        # if there is already a match, recycle the previous match
        if already_match:
            match = already_match
            serializer = serializers.MatchSerializer(match, many=False)
            return Response(
                {
                    "details": SAME_MATCH,
                    "group_match": CURRENT,
                    "match_data": serializer.data,
                }
            )

        # if the current profile did not has any previous match, then create a new match
        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        current_group.matches.add(match)
        current_group.save()
        match_serializer = serializers.MatchSerializer(match, many=False)
        return Response(
            {
                "details": NEW_MATCH,
                "group_match": CURRENT,
                "match_data": match_serializer.data,
            }
        )

    return Response({"details": LIKE})


def like_group_to_group(current_profile, current_group, liked_group):
    # add the like
    liked_group.likes.add(current_profile)

    # check if the groups have any matches in common
    group_already_matched = check_two_group_has_match(current_group, liked_group)
    if group_already_matched:
        return Response({"details": ALREADY_MATCHED})

    # get all the members who have already liked my group
    members = []
    for member in liked_group.members.all():
        if current_group.likes.filter(id=member.id).exists():
            members.append(member)

    if len(members) > 0:
        for member in members:
            already_matched = check_two_profiles_have_match(
                current_profile.id, member.id
            )
            # make a match with a member that does not have a previous match
            if not already_matched:
                match = models.Match.objects.create(
                    profile1=current_profile, profile2=member
                )
                match.save()
                liked_group.matches.add(match)
                liked_group.save()

                match_serializer = serializers.MatchSerializer(match, many=False)
                return Response(
                    {
                        "details": NEW_MATCH,
                        "group_match": BOTH,
                        "match_data": match_serializer.data,
                    }
                )

        # if there is no member with which it does not have a match, recycle the previous match
        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(match, many=False)
                return Response(
                    {
                        "details": SAME_MATCH,
                        "group_match": BOTH,
                        "match_data": match_serializer.data,
                    }
                )

    return Response({"details": LIKE})


class SwipeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        current_profile = request.user
        profiles = models.Profile.objects.all().filter(has_account=True)
        groups = models.Group.objects.all()

        if not current_profile.has_account or not current_profile.age:
            return Response(
                {"details": "You need an account to perform this action"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if current_profile.location == None:
            return Response(
                {
                    "details": "You need to set your current location to perform this action"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # all the profiles by distance
        profiles_by_distance = profiles.filter(
            location__distance_lt=(current_profile.location, D(km=8))
        )

        groups_by_distance = groups.filter(members__in=profiles_by_distance)

        # swipe filters
        show_profiles = filter_profiles(current_profile, profiles_by_distance)
        show_groups = filter_groups(current_profile, groups_by_distance)

        # Serialize data
        profiles_serializer = serializers.SwipeProfileSerializer(
            show_profiles, many=True
        )

        groups_serializer = serializers.SwipeGroupSerializer(show_groups, many=True)

        # show the groups first then the single profiles
        data = groups_serializer.data + profiles_serializer.data  # type: ignore

        # Custom respomse
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

    @action(detail=False, methods=["get"], url_path=r"actions/get-swipe-profile")
    def get_swipe_profile(self, request):
        # get the current user as a profile or the group if he is an group
        current_profile = request.user
        if current_profile.member_group.all().exists():
            current_group = current_profile.member_group.all()[0]
            group_serializer = serializers.SwipeGroupSerializer(
                current_group, many=False
            )
            return Response(group_serializer.data)

        profile_serializer = serializers.SwipeProfileSerializer(
            current_profile, many=False
        )
        return Response(profile_serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/like")
    def like(self, request, pk=None):
        current_profile = request.user
        # profile to give like
        liked_profile = models.Profile.objects.get(pk=pk)

        current_is_in_group = current_profile.member_group.all().exists()
        liked_is_in_group = liked_profile.member_group.all().exists()

        # check for one to one
        if not current_is_in_group and not liked_is_in_group:
            return like_one_to_one(current_profile, liked_profile)

        # like one to group
        if not current_is_in_group and liked_is_in_group:
            liked_group = liked_profile.member_group.all()[0]
            return like_one_to_group(current_profile, liked_group)

        # like group to one
        if current_is_in_group and not liked_is_in_group:
            current_group = current_profile.member_group.all()[0]
            return like_group_to_one(current_profile, current_group, liked_profile)

        # like group to group
        if current_is_in_group and liked_is_in_group:
            current_group = current_profile.member_group.all()[0]
            liked_group = liked_profile.member_group.all()[0]
            return like_group_to_group(current_profile, current_group, liked_group)

        return Response(
            {"details": "Something went wrong when giving like"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"], url_path=r"actions/unlike")
    def unlike(self, request, pk=None):
        # unlike profile - unlike profile or group that I already gave like previously
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
        # remove a like from my many to many field
        current_profile = request.user
        current_profile.likes.remove(pk)
        return Response({"details": "Like removed"})

    @action(detail=False, methods=["get"], url_path=r"actions/get-likes")
    def list_likes(self, request):
        current_profile = request.user
        likes = current_profile.likes.all()

        # list of tuples with the two matched profiles ids
        current_matches_ids = models.Match.objects.filter(
            Q(profile1=current_profile.id) | Q(profile2=current_profile.id)
        ).values_list("profile1", "profile2")

        # going two the list and tuples to exclude the likes
        if len(current_matches_ids) > 0:
            for i in range(len(current_matches_ids)):
                likes = likes.exclude(id__in=current_matches_ids[i])

        profiles = []
        groups = []

        for like_profile in likes:
            if like_profile.member_group.all().exists():
                groups.append(like_profile.member_group.all()[0])
            else:
                profiles.append(like_profile)

        groups_serializer = serializers.SwipeGroupSerializer(groups, many=True)
        profiles_serializer = serializers.SwipeProfileSerializer(profiles, many=True)
        data = groups_serializer.data + profiles_serializer.data
        return Response({"count": likes.count(), "results": data})


class MatchModelViewSet(ModelViewSet):
    queryset = models.Match.objects.all()
    serializer_class = serializers.MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if (
            self.action == "list"
            or self.action == "retrieve"
            or self.action == "create"
            or self.action == "update"
        ):
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=["get"], url_path=r"actions/list-profile-matches")
    def list_profile_matches(self, request):
        current_profile = request.user
        matches = models.Match.objects.filter(
            Q(profile1=current_profile.id) | Q(profile2=current_profile.id)
        )
        serializer = serializers.MatchSerializer(matches, many=True)
        return Response({"count": matches.count(), "data": serializer.data})

    def destroy(self, request, pk=None):
        current_profile = request.user

        try:
            match = models.Match.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"details": "Match does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        matched_profile = get_matched_profile(current_profile, match)
        matched_profile.likes.remove(current_profile)
        current_profile.likes.remove(matched_profile)
        match.delete()

        return Response({"details": "Match deleted"}, status=status.HTTP_200_OK)
