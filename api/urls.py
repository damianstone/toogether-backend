from django.urls import path, include
from rest_framework import routers
from api.views import profile_views, group_views, swipe_views
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

urlpatterns = [
    # Internal endpoints
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
    path("internal/groups/", internal_group.list_groups, name="list_groups"),
    path(
        "internal/groups/<pk>/",
        internal_group.get_group,
        name="get_group",
    ),
    path(
        "internal/groups/<pk>/",
        internal_group.add_member,
        name="add_member",
    ),
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
    # Public endpoints - authentication
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "users/login/",
        profile_views.MyTokenObtainPairView.as_view(),
        name="login",
    ),
    # Public endpoints
    path("", include(router.urls)),
]
