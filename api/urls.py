from django.urls import path, include
from rest_framework import routers
from api.views import profile_views, group_views, swipe_views, chat_views
from api.internal import internal_profile, internal_group, internal_swipe
from rest_framework_simplejwt.views import TokenRefreshView


router = routers.DefaultRouter()

router.register(
    r"profiles",
    profile_views.ProfileViewSet,
    basename="profile",
)

router.register(
    r"photos",
    profile_views.PhotoViewSet,
    basename="photo",
)

router.register(
    r"groups",
    group_views.GroupViewSet,
    basename="group",
)

router.register(
    r"swipe",
    swipe_views.SwipeModelViewSet,
    basename="swipe",
)

router.register(
    r"matches",
    swipe_views.MatchModelViewSet,
    basename="match",
)

router.register(
    r"conversations",
    chat_views.ConversationViewSet,
    basename="conversation",
)

router.register(
    r"group-chat",
    chat_views.MyGroupViewSet,
    basename="group-chat",
)

urlpatterns = [
    # !!Internal endpoints - profiles
    path("internal/profiles/", internal_profile.list_profiles, name="list_profiles"),
    path(
        "internal/profiles/<pk>/",
        internal_profile.delete_profile,
        name="delete_profile",
    ),
    path(
        "internal/generate-profiles/",
        internal_profile.generated_profiles,
        name="generate_profiles",
    ),
    path(
        "internal/delete-all-profiles/",
        internal_profile.delete_all_profiles,
        name="delete_all_profiles",
    ),
    # !!Internal production endpoints - groups
    path("internal/groups/", internal_group.list_groups, name="list_groups"),
    path(
        "internal/groups/<pk>/",
        internal_group.get_group,
        name="get_group",
    ),
    path(
        "internal/groups/<pk>/actions/add-member/",
        internal_group.add_member,
        name="add_member",
    ),
    path(
        "internal/groups/actions/ungroup-users/",
        internal_group.ungroup_users,
        name="ungroup_users",
    ),
    # !!Internal development endpoints - groups
    path(
        "internal/generate-groups/",
        internal_group.generate_groups,
        name="generate_groups",
    ),
    path(
        "internal/delete-all-groups/",
        internal_group.delete_all_groups,
        name="delete_all_groups",
    ),
    path(
        "internal/check-groups/",
        internal_group.check_groups,
        name="check_groups",
    ),
    # !!Internal endpoints - swipe
    path("internal/matches/", internal_swipe.list_matches, name="list_matches"),
    path(
        "internal/matches/<pk>/",
        internal_swipe.get_match,
        name="get_match",
    ),
    path(
        "internal/generate-likes/",
        internal_swipe.generate_likes,
        name="generate_likes",
    ),
    path(
        "internal/remove-all-likes/",
        internal_swipe.remove_all_likes,
        name="remove_all_likes",
    ),
    path(
        "internal/unlike-all/",
        internal_swipe.unlike_all,
        name="unlike_all",
    ),
    # !!Public endpoints - authentication
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "users/login/",
        profile_views.MyTokenObtainPairView.as_view(),
        name="login",
    ),
    path("users/recovery-code/", profile_views.recovery_code, name="recovery_code"),
    path("users/validate-code/", profile_views.validate_code, name="validate_code"),
    # !!Public endpoints -  ModelViewSets
    path("", include(router.urls)),
]
