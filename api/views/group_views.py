from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers


class GroupViewSet(ModelViewSet):
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [IsAuthenticated]

    # TODO: generate the share link before create the group
    # TODO: add property to know if its a male or female group
    def create(self, request):
        profile = request.user
        profile_has_group = models.Group.objects.filter(owner=profile.id).exists()
        profile_is_in_another_group = profile.member_profiles.all().exists()
        fields_serializer = serializers.GroupSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)
        # TODO: check if the user has already created a group
        if profile_has_group:
            return Response(
                {"detail": "You already have a group created"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: check if the user is already in another group
        if profile_is_in_another_group:
            return Response(
                {"detail": "you are already in a group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = models.Group.objects.create(
            owner=profile, share_link=fields_serializer._validated_data["share_link"]
        )

        group.members.add(profile)
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

    # TODO: owner: delete the group (DELETE)
    def destroy(self, request, pk):
        profile = request.user
        try:
            group = models.Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Group does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if profile != group.owner:
            return Response(
                {"detail": "You do not have permissions to perform this action"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        group.delete()
        return Response(
            {"detail": "Group deleted"},
            status=status.HTTP_200_OK,
        )

    # TODO: add member to a group checking the share_link (POST)
    @action(detail=False, methods=["post"], url_path=r"actions/join")
    def join(self, request):
        profile = request.user
        profile_has_group = models.Group.objects.filter(owner=profile.id).exists()
        profile_is_in_another_group = profile.member_profiles.all().exists()
        fields_serializer = serializers.GroupSerializer(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        if profile_has_group:
            return Response(
                {"detail": "You already have a group created"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: check if the user is already in another group
        if profile_is_in_another_group:
            return Response(
                {"detail": "you are already in a group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            group = models.Group.objects.get(
                share_link=fields_serializer._validated_data["share_link"]
            )
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Group does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.add(profile)
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

    # TODO: leave the group (checking for owner) (POST)
    @action(detail=True, methods=["post"], url_path=r"actions/leave")
    def leave(self, request, pk=None):
        profile = request.user

        try:
            group = models.Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Group does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile == group.owner:
            return Response(
                {
                    "detail": "This group is created by you, if you leave it will be deleted"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.remove(profile)
        return Response(
            {"detail": "You left the group"},
            status=status.HTTP_200_OK,
        )

    # TODO: owner: remove member from the group (POST)
    @action(detail=True, methods=["post"], url_path=r"actions/remove-member")
    def remove_member(self, request, pk=None):
        profile = request.user
        fields_serializer = serializers.GroupSerializerWithMember(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        try:
            group = models.Group.objects.get(pk=pk)
            profile_to_remove = models.Profile.objects.get(
                id=fields_serializer._validated_data["member_id"]
            )
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Object does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile != group.owner:
            return Response(
                {"detail": "You do not have permissions to perform this action"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
        group.members.remove(profile_to_remove)
        return Response(
            {"detail": "Member removed"},
            status=status.HTTP_200_OK,
        )
