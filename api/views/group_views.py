from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers

# Response constants
NO_GROUP = "NO_GROUP"


class GroupViewSet(ModelViewSet):
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(
            {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
        )

    def retrieve(self, request, pk=None):
        return Response(
            {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
        )

    def create(self, request):
        current_profile = request.user

        if current_profile.member_group.all().exists():
            return Response(
                {"detail": "You are already a member of a group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = models.Group.objects.create(owner=current_profile)
        group.members.add(current_profile)
        current_profile.is_in_group = True

        group.save()
        current_profile.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data)

    def update(self, request, pk=None):
        return Response(
            {"detail": "Not authorized"}, status=status.HTTP_401_UNAUTHORIZED
        )

    def destroy(self, request, pk=None):
        current_profile = request.user
        try:
            group = models.Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Group does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current_profile != group.owner:
            return Response(
                {"detail": "You do not have permissions to perform this action"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # change the property before delete the group
        for member in group.members.all():
            member.is_in_group = False
            member.save()

        group.delete()
        return Response(
            {"detail": "Group deleted"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path=r"actions/get-group")
    def get_group(self, request):
        current_profile = request.user

        if current_profile.member_group.all().exists():
            group = current_profile.member_group.all()[0]
            serializer = serializers.GroupSerializer(group, many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({"detail": NO_GROUP}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path=r"actions/join")
    def join(self, request):
        current_profile = request.user
        fields_serializer = serializers.GroupSerializerWithLink(data=request.data)
        fields_serializer.is_valid(raise_exception=True)

        if current_profile.member_group.all().exists():
            return Response(
                {"detail": "You are already a member of a group"},
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

        group.members.add(current_profile)
        current_profile.is_in_group = True

        current_profile.save()
        group.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path=r"actions/leave")
    def leave(self, request, pk=None):
        current_profile = request.user

        try:
            group = models.Group.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Group does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current_profile.id == group.owner.id:
            group.delete()
            return Response(
                {"detail": "Group deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.remove(current_profile)
        current_profile.is_in_group = False

        group.save()
        current_profile.save()
        return Response(
            {"detail": "You left the group"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path=r"actions/remove-member")
    def remove_member(self, request, pk=None):
        current_profile = request.user
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

        if current_profile.id != group.owner.id:
            return Response(
                {"detail": "You do not have permissions to perform this action"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group.members.remove(profile_to_remove)
        profile_to_remove.is_in_group = False

        profile_to_remove.save()
        group.save()
        serializer = serializers.GroupSerializer(group, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
