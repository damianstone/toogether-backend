from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.gis.measure import D
from django.db.models import Q
from api import models, serializers

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


def like_one_to_one(request, current_profile, liked_profile):
    # like the profile
    liked_profile.likes.add(current_profile)

    # check if the current profile is already a like of the liked_profile (mutual like)
    if current_profile.likes.filter(id=liked_profile.id).exists():

        already_matched = check_two_profiles_have_match(
            current_profile.id, liked_profile.id
        )

        if already_matched:
            return Response({"details": ALREADY_MATCHED}, status=status.HTTP_200_OK)

        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        match_serializer = serializers.MatchSerializer(
            match, many=False, context={"request": request}
        )
        return Response(
            {
                "details": NEW_MATCH,
                "group_match": NEITHER,
                "match_data": match_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    return Response({"details": LIKE}, status=status.HTTP_200_OK)


def like_one_to_group(request, current_profile, liked_group):
    liked_group.likes.add(current_profile)

    # check if the current profile has already a match with the group
    already_matched = check_profile_group_has_match(current_profile.id, liked_group)
    if already_matched:
        return Response({"details": ALREADY_MATCHED}, status=status.HTTP_200_OK)

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

                match_serializer = serializers.MatchSerializer(
                    match, many=False, context={"request": request}
                )

                return Response(
                    {
                        "details": NEW_MATCH,
                        "group_match": LIKED,
                        "match_data": match_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        # if there is no member with which it does not have a match, recycle the previous match
        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(
                    match, many=False, context={"request": request}
                )
                return Response(
                    {
                        "details": SAME_MATCH,
                        "group_match": LIKED,
                        "match_data": match_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

    return Response({"details": LIKE}, status=status.HTTP_200_OK)


def like_group_to_one(request, current_profile, current_group, liked_profile):
    # add the like
    liked_profile.likes.add(current_profile)

    # check if the liked profile has already a match with the group
    already_matched = check_profile_group_has_match(liked_profile.id, current_group)
    if already_matched:
        return Response({"details": ALREADY_MATCHED}, status=status.HTTP_200_OK)

    # check if liked profile already like the group (mutual like)
    # if there is a mutal like and a match has not been found in the foor,
    # so it is because it must be the first member to like the profile
    if current_group.likes.filter(id=liked_profile.id).exists():
        # check if the current user has already a match with the liked profile
        already_match = get_match(current_profile.id, liked_profile.id)
        # if there is already a match, recycle the previous match
        if already_match:
            match = already_match
            serializer = serializers.MatchSerializer(
                match, many=False, context={"request": request}
            )
            return Response(
                {
                    "details": SAME_MATCH,
                    "group_match": CURRENT,
                    "match_data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        # if the current profile did not has any previous match, then create a new match
        match = models.Match.objects.create(
            profile1=current_profile, profile2=liked_profile
        )
        match.save()
        current_group.matches.add(match)
        current_group.save()
        match_serializer = serializers.MatchSerializer(
            match, many=False, context={"request": request}
        )
        return Response(
            {
                "details": NEW_MATCH,
                "group_match": CURRENT,
                "match_data": match_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    return Response({"details": LIKE}, status=status.HTTP_200_OK)


def like_group_to_group(request, current_profile, current_group, liked_group):
    # add the like
    liked_group.likes.add(current_profile)

    # check if the groups have any matches in common
    group_already_matched = check_two_group_has_match(current_group, liked_group)
    if group_already_matched:
        return Response({"details": ALREADY_MATCHED}, status=status.HTTP_200_OK)

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

                match_serializer = serializers.MatchSerializer(
                    match, many=False, context={"request": request}
                )
                return Response(
                    {
                        "details": NEW_MATCH,
                        "group_match": BOTH,
                        "match_data": match_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        # if there is no member with which it does not have a match, recycle the previous match
        for member in members:
            if get_match(current_profile.id, member.id):
                match = get_match(current_profile.id, member.id)
                match_serializer = serializers.MatchSerializer(
                    match, many=False, context={"request": request}
                )
                return Response(
                    {
                        "details": SAME_MATCH,
                        "group_match": BOTH,
                        "match_data": match_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

    return Response({"details": LIKE}, status=status.HTTP_200_OK)
