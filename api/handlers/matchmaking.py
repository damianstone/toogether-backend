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

"""
    Given a current_profile and a match object, returns the profile of the match
    that is not the current_profile.
    
    @param current_profile: the profile object of the current user
    @param match: the match object containing the two profiles
    @return: the profile object of the other user in the match
"""


def get_matched_profile(current_profile, match):
    if current_profile.id == match.profile1.id:
        return match.profile2
    return match.profile1


"""
    Given two profile IDs, checks if they have already matched.
    
    @param profile1_id: the ID of the first profile
    @param profile2_id: the ID of the second profile
    @return: True if the two profiles have already matched, False otherwise
"""


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


"""
    Given a profile ID and a group object, checks if the profile has a match with any member
    of the group.
    
    @param profile_id: the ID of the profile
    @param group: the group object to check for matches
    @return: True if the profile has a match with any member of the group, False otherwise
"""


def check_profile_group_has_match(profile_id, group):
    current_profile_matches = models.Match.objects.filter(
        Q(profile1=profile_id) | Q(profile2=profile_id)
    )

    # it is a many to many
    group_matches = group.matches.all()

    print(current_profile_matches.filter(id__in=group_matches).exists())
    
    if current_profile_matches.filter(id__in=group_matches).exists():
        return True

    return False


"""
    Given two group objects, checks if they have any matches in common.
    
    @param group1: the first group object
    @param group2: the second group object
    @return: True if the two groups have matches in common, False otherwise
"""


def check_two_group_has_match(group1, group2):
    group1_matches = group1.matches.all()
    group2_matches = group2.matches.all()

    if group1_matches.filter(id__in=group2_matches).exists():
        return True

    return False


"""
    Given two profile IDs, retrieves the match object between the two profiles.
    
    @param profile1_id: the ID of the first profile
    @param profile2_id: the ID of the second profile
    @return: the match object between the two profiles, or False if no match exists
"""


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


"""
    Like a profile and create a match if it is a mutual like
    @param request - the HTTP request
    @param current_profile - the profile that gives the like
    @param liked_profile - the profile that receives the like
    @return HTTP response with JSON object containing match details if it is a mutual like,
    or a response indicating that the like was successful if it is not
"""


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


"""
    Add a like for the current user to the liked group.

    If the current user has already matched with the group, return a response indicating so.
    Otherwise, get all members who have liked the current user and try to create a match with them.
    If a match is successfully created, return a response indicating a new match has been created.
    If no match is created, try to recycle a previous match with a member who has liked the current user.
    If no match can be recycled, return a response indicating the user has liked the group.

    @param request - the HTTP request object
    @param current_profile - the user profile object representing the current user
    @param liked_group - the group object that the user has liked
    @return - an HTTP response object with a JSON payload indicating the status of the operation
"""


def like_one_to_group(request, current_profile, liked_group):
    liked_group.likes.add(current_profile)

    # check if the current profile has already matched with the group
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
                # create a match
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


"""
    Add a like from a group to a profile and check if there is a match or a previous match 
    with the group.

    @param request - the request object
    @param current_profile - the profile of the user making the like
    @param current_group - the group from which the like is made
    @param liked_profile - the profile to which the like is made

    @return Response - a response object with the result of the like action
"""


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


"""
    This function adds a like from the current profile to the liked group, checks if there are any matches between the current group
    and the liked group, and attempts to create a match with a member from the liked group that has liked the current group.

    @param request: The request object.
    @param current_profile: The profile that is making the like.
    @param current_group: The group that the current_profile belongs to.
    @param liked_group: The group that the current_profile is liking.
    @return: A Response object with details on the status of the like.
"""


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
