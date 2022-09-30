from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers


# TODO: implement web sockets


class SwipeModelViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    # TODO: not display the profile of the current user
    def get_queryset(self):
        groups = models.Group.objects.all()
        current_profile = models.Profile.objects.filter(user=self.request.user)
        
        if current_profile.is_in_group:
            print(current_profile.is_in_group)
            for group in groups:
                # filter the members and exclude the owner
                members_without_owner = group.members.exclude(id=group.owner.id)
        else:
            return models.Profile.objects.filter(user=self.request.user).exclude(
                user=self.request.user
            )


    # TODO: check if the user belong to a many to many field
    def list(self, request):
        # get the current user
        profile = models.Profile.objects.get(id=request.user.id)
        show_gender = profile.show_me
        print(show_gender)  # M, W, X -> X means Man and Woman

        # get all the profiles and groups (queryes)
        profiles = models.Profile.objects.all().filter(has_account=True)
        groups = models.Group.objects.all()

        # TODO: check if profile is in blocked profiles
        # TODO: check if user
        # filtering the groups and profiles by  gender
        profiles_not_in_group = profiles.filter(is_in_group=False)
        
        if show_gender == "X":
            show_profiles = profiles_not_in_group
            show_groups = groups
        else:
            show_profiles = profiles_not_in_group.filter(gender=show_gender)
            show_groups = groups.filter(gender=show_gender)

        # Serialize data
        profiles_serializer = serializers.SwipeProfileSerializer(
            show_profiles, many=True
        )
        groups_serializer = serializers.SwipeGroupSerializer(show_groups, many=True)
        data = profiles_serializer.data + groups_serializer.data

        # Custom respomse
        return Response(
            {
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


# TODO: list all the users and groups filtering by location

# TODO: get one profile using the swipe serializer

# TODO: get one group with swipe serializer

# TODO: like action

# TODO: check if both like each other and create a match

# TODO: check if a match was alread showed
