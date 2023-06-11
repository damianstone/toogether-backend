from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from api import models, serializers
from django.utils import timezone
from datetime import timedelta
import random


# * List groups
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_groups(request):
    groups = models.Group.objects.all()
    serializer = serializers.GroupSerializer(groups, many=True)
    return Response(
        {"count": groups.count(), "results": serializer.data},
        status=status.HTTP_200_OK,
    )


# * Retrieve a group
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_group(request, pk=None):
    try:
        group = models.Group.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Object does not exist"}, status=status.HTTP_400_BAD_REQUEST
        )

    serializer = serializers.GroupSerializer(group, many=False)
    return Response(
        serializer.data,
        status=status.HTTP_200_OK,
    )


# * Add any member to any group
@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_member(request, pk=None):
    data = request.data
    member_id = data["member_id"]
    try:
        group = models.Group.objects.get(pk=pk)
        member = models.Profile.objects.get(id=member_id)
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Object does not exist"}, status=status.HTTP_400_BAD_REQUEST
        )
    group.members.add(member)
    group.save()

    serializer = serializers.GroupSerializer(group, many=False)
    return Response(serializer.data)


# * Generate fake groups
@api_view(["POST"])
@permission_classes([IsAdminUser])
def generate_groups(request):
    current_user = request.user
    # check not making this request in production
    if not settings.DEBUG:
        return Response(
            {"error": "This action cannot be performed in production"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # get all profiles and exclude the owner
    profiles = models.Profile.objects.exclude(id=current_user.id)

    # calculate number of groups to generate (5% of total profiles)
    num_groups = int(len(profiles) * 0.2)

    # create empty list to hold generated groups
    group_list = []

    while len(group_list) < num_groups:
        # random number of members for the next group
        num_members = random.randint(2, 6)

        members_to_add = []

        # get the members to add in the group
        while len(members_to_add) < num_members:
            # filter out profiles that already belong to a group
            eligible_profiles = profiles.exclude(member_group__isnull=False)

            # select a random profile from the eligible profiles
            profile_to_add = random.choice(eligible_profiles)

            # check that the selected profile is not already in the members_to_add list
            if profile_to_add not in members_to_add:
                members_to_add.append(profile_to_add)

        # first of members to add will be the owner
        owner = members_to_add[0]

        # create the group
        group = models.Group.objects.create(owner=owner)

        # add all the members (profiles) that does not belong to any group yet
        for member in members_to_add:
            group.members.add(member)
            member.is_in_group = True
            member.save()

        group.save()
        group_list.append(group)

    serializer = serializers.GroupSerializer(group_list, many=True)
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )


# * delete all the groups
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_all_groups(request):
    # check not making this request in production
    if not settings.DEBUG:
        return Response(
            {"error": "This action cannot be performed in production"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    groups = models.Group.objects.all()

    for group in groups:
        for member in group.members.all():
            member.is_in_group = False
            member.save()

        group.delete()

    return Response({"detail": f"{len(groups)} groups deleted"})


# * check user with more than one group
@api_view(["GET"])
@permission_classes([IsAdminUser])
def check_groups(request):
    profiles = models.Profile.objects.all()

    num_of_fails = []
    for profile in profiles:
        if profile.member_group.all().count() > 1:
            num_of_fails.append(profile)

    return Response(
        {"detail": f"{len(num_of_fails)} profiles belong to more than one group"}
    )


# * Ungroup groups with just 1 member
@api_view(["POST"])
@permission_classes([IsAdminUser])
def ungroup_users(request):
    groups = models.Group.objects.all()

    ungroupped = 0

    for group in groups:
        if group.members.all().count() == 1:
            print(group.members.all().count() == 1)
            # check when the group was created and delete it if it was created more than 1 day ago
            if group.created_at < timezone.now() - timedelta(days=1):
                for member in group.members.all():
                    member.is_in_group = False
                    member.save()
                group.delete()
                ungroupped += 1

    return Response({"detail": f"{ungroupped} groups with just 1 member deleted"})
