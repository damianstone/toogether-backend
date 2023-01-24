from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers


class GroupViewSet(ModelViewSet):
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [IsAuthenticated]

    # Internal endpoints
    def get_permissions(self):
        if (
            self.action == "list"
            or self.action == "update"
            or self.action == "add_member"
        ):
            return [IsAdminUser()]
        return [permission() for permission in self.permission_classes]

    def create(self, request):
        profile = request.user
        profile_has_group = models.Group.objects.filter(owner=profile.id).exists()
        profile_is_in_another_group = profile.member_group.all().exists()

        fields_serializer = serializers.GroupSerializer(data={"gender": profile.gender})
        fields_serializer.is_valid(raise_exception=True)

        if profile_has_group:
            return Response(
                {"detail": "You already have a group created"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile_is_in_another_group:
            return Response(
                {"detail": "you are already in a group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = models.Group.objects.create(owner=profile)
        group.members.add(profile)
        profile.is_in_group = True
        group.total_members = 1
        group.gender = fields_serializer._validated_data["gender"]

        group.save()
        profile.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

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
        profile.is_in_group = False
        profile.save()
        return Response(
            {"detail": "Group deleted"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path=r"actions/join")
    def join(self, request):
        profile = request.user
        profile_has_group = models.Group.objects.filter(owner=profile.id).exists()
        profile_is_in_another_group = profile.member_group.all().exists()
        fields_serializer = serializers.GroupSerializerWithLink(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        if profile_has_group:
            return Response(
                {"detail": "You already have a group created"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        group.total_members += 1
        profile.is_in_group = True
        group.save()
        profile.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

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
        group.total_members -= 1
        profile.is_in_group = False
        group.save()
        profile.save()
        return Response(
            {"detail": "You left the group"},
            status=status.HTTP_200_OK,
        )

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
        group.total_members -= 1
        profile_to_remove.is_in_group = False
        group.save()
        profile.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path=r"actions/add-member")
    def add_member(self, request, pk=None):
        fields_serializer = serializers.GroupSerializerWithMember(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        try:
            group = models.Group.objects.get(pk=pk)
            profile_to_add = models.Profile.objects.get(
                id=fields_serializer._validated_data["member_id"]
            )
            
            # check if the profile to add is in another group
            profile_has_group = models.Group.objects.filter(owner=profile_to_add.id).exists()
            profile_is_in_another_group = profile_to_add.member_group.all().exists()
            
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Object does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile_has_group or profile_is_in_another_group:
            return Response(
                {"detail": "The member is already in another group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.add(profile_to_add)
        group.total_members += 1
        profile_to_add.is_in_group = True
        group.save()
        profile_to_add.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)
