from django.urls import path, include
from rest_framework import routers
from api.views import profile_views, group_views, swipe_views
from api.internal import internal_profile
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
        "internal/delete-all/",
        internal_profile.delete_all,
        name="delete_all",
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
