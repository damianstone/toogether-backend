from django.utils.timezone import now
from datetime import date


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
        show_groups = show_groups.filter(age__gte=profile_age, age__lte=profile_age + 6)
    else:
        show_groups = show_groups.filter(
            age__gte=profile_age - 5, age__lte=profile_age + 5
        )

    # the group needs a minimum of two members to be displayed
    show_groups = show_groups.filter(total_members__gte=2)

    # filter all the groups that has a like from the current profile
    groups_liked_by_current_profile = show_groups.filter(likes=current_profile.id)

    # exclude liked groups
    show_groups = show_groups.exclude(id__in=groups_liked_by_current_profile)

    return show_groups
