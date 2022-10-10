from unicodedata import name
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers
from datetime import date
from django.utils.timezone import now
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.db.models import Q
import random


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
    for blocked_profile in blocked_profiles:
        show_profiles = show_profiles.exclude(id=blocked_profile.id)

    # exclude any profile that has blocked the current user
    if current_profile.blocked_by.all().exists():
        for blocked_by_profile in current_profile.blocked_by.all():
            show_profiles = show_profiles.exclude(id=blocked_by_profile.id)

    # Show profiles between in a range of ages
    if profile_age == 18 or profile_age == 19:
        show_profiles = age_range(show_profiles, profile_age - 1, profile_age + 6)
    else:
        show_profiles = age_range(show_profiles, profile_age - 5, profile_age + 5)

    # exclude the current user in the swipe
    show_profiles = show_profiles.exclude(id=current_profile.id)

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
    if current_profile.is_in_group:
        for group in groups:
            if group.members.filter(id=current_profile.id).exists():
                show_groups = show_groups.exclude(id=group.id)

    # TODO: implement a search algorithm (hash map)
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

    return show_groups


def check_two_profiles_have_match(profile1_id, profile2_id):
    current_matches = models.Match.objects.filter(
        Q(profile1=profile1_id) | Q(profile2=profile1_id)
    )

    print("current_matches ", current_matches)

    liked_matches = models.Match.objects.filter(
        Q(profile1=profile2_id) | Q(profile2=profile2_id)
    )

    print("liked_matches ", liked_matches)

    if current_matches.filter(id__in=liked_matches).exists():
        # return the match
        return True

    return False


def check_profile_group_has_match(profile_id, group):
    current_profile_matches = models.Match.objects.filter(
        Q(profile1=profile_id) | Q(profile2=profile_id)
    )

    print("current_profile_matches -> ", current_profile_matches)

    # it is a many to many
    group_matches = group.matches.all()

    print("group_matches -> ", group_matches)

    if current_profile_matches.filter(id__in=group_matches).exists():
        return True

    return False


def check_two_group_has_match(group1, group2):
    group1_matches = group1.matches.all()
    group2_matches = group2.matches.all()

    print("group mayched", group1_matches, group2_matches)

    if group1_matches.filter(id__in=group2_matches).exists():
        return True

    return False


def get_match(profile1_id, profile2_id):
    current_matches = models.Match.objects.filter(
        Q(profile1=profile1_id) | Q(profile2=profile1_id)
    )

    print("current_matches ", current_matches)

    liked_matches = models.Match.objects.filter(
        Q(profile1=profile2_id) | Q(profile2=profile2_id)
    )

    print("liked_matches ", liked_matches)

    if current_matches.filter(id__in=liked_matches).exists():
        return current_matches.filter(id__in=liked_matches)

    return False


def like_one_to_one(current_profile, liked_profile):
    # like the profile
    liked_profile.likes.add(current_profile)

    # check if the current profile is already a like of the liked_profile,
    # if true its a match - eso quiere decir que le dio like a alguien que ya le puse like a el
    if current_profile.likes.filter(id=liked_profile.id).exists():

        already_matched = check_two_profiles_have_match(
            current_profile.id, liked_profile.id
        )

        if already_matched:
            return Response({"details": "match already exists"})

        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        match_serializer = serializers.MatchSerializer(match, many=False)
        return Response({"details": "its a match", "match_data": match_serializer.data})

    return Response({"details": "like gived"})


def like_one_to_group(current_profile, liked_group):
    liked_group.likes.add(current_profile)

    # check if two models has the same value in a many to many field
    # eso quiere decir que este perfil ya ha hecho match con este grupo
    # basicamente se le repetio en el swipe list
    already_matched = check_profile_group_has_match(current_profile.id, liked_group)
    if already_matched:
        return Response({"details": "match already exists"})

    # get the member that has given the like
    members = []
    for member in liked_group.members.all():
        if current_profile.likes.filter(id=member.id).exists():
            members.append(member)

    if len(members) > 0:
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
                    {"new_match": "group match", "match_data": match_serializer.data}
                )

        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(match[0], many=False)
                return Response(
                    {"same_match": "group match", "match_data": match_serializer.data}
                )

    return Response({"details": "like gived"})


def like_group_to_one(current_profile, current_group, liked_profile):
    # add the like
    liked_profile.likes.add(current_profile)

    # check if two models has the same value in a many to many field
    # check if the group already has a match with the profile
    already_matched = check_profile_group_has_match(liked_profile.id, current_group)
    if already_matched:
        return Response({"details": "match already exists"})

    # check if the user already like the group
    # si el perfil ya le habia puesto like y no se ha encontrado ningun match en el foor loop de antes
    # entonces debe ser pq este es el primer miembro en darle like a este perfil
    if current_group.likes.filter(id=liked_profile.id).exists():
        # check if the current user has already a match with the liked profile
        already_match = get_match(current_profile.id, liked_profile.id)
        # si ya tiene un match cn ese perfil entonces no crear otro match object
        if already_match:
            match = already_match[0]
            serializer = serializers.MatchSerializer(match, many=False)
            return Response(
                {
                    "same_match": "same match",
                    "match_data": serializer.data,
                }
            )

        # si es que el current profile no tenia un match ya con ese perfil, entonces crearlo
        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        current_group.matches.add(match)
        current_group.save()
        match_serializer = serializers.MatchSerializer(match, many=False)
        return Response(
            {"new_match": "group match", "match_data": match_serializer.data}
        )

    # si al usuario no le ha gustado el group entonces solo dar like
    return Response({"details": "like gived"})


def like_group_to_group(current_profile, current_group, liked_group):
    # add the like
    liked_group.likes.add(current_profile)

    # check si los grupos tienen algun match en comun
    group_already_matched = check_two_group_has_match(current_group, liked_group)
    if group_already_matched:
        return Response({"details": "already matched"})

    # get tdos los miembros que ya le han dado like a mi grupo
    members = []
    for member in liked_group.members.all():
        if current_group.likes.filter(id=member.id).exists():
            members.append(member)

    if len(members) > 0:
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
                    {"new_match": "group match", "match_data": match_serializer.data}
                )

        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(match[0], many=False)
                return Response(
                    {"same_match": "group match", "match_data": match_serializer.data}
                )

    return Response({"details": "like gived"})


class SwipeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        current_profile = models.Profile.objects.get(id=request.user.id)
        profiles = models.Profile.objects.all().filter(has_account=True)
        groups = models.Group.objects.all()

        # all the profiles by distance
        profiles_by_distance = profiles.filter(
            location__distance_lt=(current_profile.location, D(km=8))
        )

        groups_by_distance = models.Group.objects.none()

        # get the groups that contain users in the distance ratio
        for profile in profiles_by_distance:
            # check if the profile is in a group
            if profile.member_group.all().exists():
                # if at least one member is i the distance ratio add the group to the swipe
                groups_by_distance = groups_by_distance.union(
                    profile.member_group.all()
                )

        # swipe filters
        show_profiles = filter_profiles(current_profile, profiles_by_distance)
        show_groups = filter_groups(current_profile, groups_by_distance)

        # Serialize data
        profiles_serializer = serializers.SwipeProfileSerializer(
            show_profiles, many=True
        )

        groups_serializer = serializers.SwipeGroupSerializer(show_groups, many=True)

        # show the groups first then the single profiles
        data = groups_serializer.data + profiles_serializer.data

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
        # TODO: check if the user in group and return the group
        serializer = serializers.SwipeProfileSerializer(profile, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=["post"], url_path=r"actions/remove-like")
    def remove_like(self, request, pk=None):
        current_profile = request.user
        current_profile.likes.remove(pk)
        return Response({"details": "Like removed"})

    @action(detail=False, methods=["get"], url_path=r"actions/get-likes")
    def list_likes(self, request):
        current_profile = request.user

        # list of tuples with the two matched profiles ids
        current_matches_ids = models.Match.objects.filter(
            Q(profile1=current_profile.id) | Q(profile2=current_profile.id)
        ).values_list("profile1", "profile2")

        # going two the list and tuples to exclude the likes
        for i in range(len(current_matches_ids)):
            likes = current_profile.likes.all().exclude(id__in=current_matches_ids[i])

        serializer = serializers.SwipeProfileSerializer(likes, many=True)
        return Response({"count": likes.count(), "results": serializer.data})


class MatchModelViewSet(ModelViewSet):
    queryset = models.Match.objects.all()
    serializer_class = serializers.MatchSerializer
    permission_classes = [IsAuthenticated]

    # TODO: just for admins
    # def get_permissions(self):
    #     if self.action == "list":
    #         return [IsAdminUser()]
    #     return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=["get"], url_path=r"actions/list-profile-matches")
    def list_profile_matches(self, request):
        current_profile = request.user
        matches = current_profile.matches.all()
        serializer = serializers.MatchSerializer(matches, many=True)
        return Response({"count": matches.count(), "data": serializer.data})

    # TODO: distroy match for both users
