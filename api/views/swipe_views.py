from unicodedata import name
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers
from datetime import date
from django.utils.timezone import now
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D


# TODO: filter groups and profiles by gender --
# TODO: Show profiles that are not in group --
# TODO: exclude blocked profiles --
# TODO: exclude the current user or the current group in the swipe list --
# TODO: filter by age --

# TODO: if the user is blocked by someone dont show that someone
# TODO: filter by distance


def age_range(data, min_age, max_age):
    current = now().date()
    min_date = date(current.year - min_age, current.month, current.day)
    max_date = date(current.year - max_age, current.month, current.day)

    return data.filter(birthdate__gte=max_date, birthdate__lte=min_date)


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

    # Show profiles between in a range of ages
    if profile_age == 18 or profile_age == 19:
        show_profiles = age_range(show_profiles, profile_age - 1, profile_age + 6)
    else:
        show_profiles = age_range(show_profiles, profile_age - 5, profile_age + 5)

    # exclude the current user in the swipe
    show_profiles = show_profiles.exclude(id=current_profile.id)

    return show_profiles


def filter_groups(current_profile, groups):
    profile_age = current_profile.age
    profile_is_in_group = current_profile.is_in_group
    blocked_profiles = current_profile.blocked_profiles.all()
    show_gender = current_profile.show_me

    # filter by gender
    if show_gender == "X":
        show_groups = groups
    else:
        show_groups = groups.filter(gender=show_gender)

    # if the user in a group, don't their group in the swipe
    if profile_is_in_group:
        for group in groups:
            if group.members.filter(id=current_profile.id).exists():
                show_groups = show_groups.exclude(id=group.id)

    # TODO: implement a search algorithm (hash map)
    # dont' show groups that has any blocked profile in their members
    for group in groups:
        for blocked_profile in blocked_profiles:
            if group.members.filter(id=blocked_profile.id).exists():
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
            #check if the profile is in a group
            if profile.member_group.all().exists():
                # if at least one member is i the distance ratio add the group to the swipe
                groups_by_distance = groups_by_distance.union(profile.member_group.all())
        
        # swipe filters
        show_profiles = filter_profiles(current_profile, profiles_by_distance)
        show_groups = filter_groups(current_profile, groups_by_distance)

        # Serialize data
        profiles_serializer = serializers.SwipeProfileSerializer(
            show_profiles, many=True
        )
        
        groups_serializer = serializers.SwipeGroupSerializer(show_groups, many=True)
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


# TODO: list all the users and groups filtering by location

# TODO: get one profile using the swipe serializer

# TODO: get one group with swipe serializer

# TODO: like action

# TODO: check if both like each other and create a match

# TODO: check if a match was alread showed
