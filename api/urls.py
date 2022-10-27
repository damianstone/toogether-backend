from django.urls import path, include
from rest_framework import routers
from api.views import profile_views, group_views, swipe_views
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
    path("token/", profile_views.getUsers.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", profile_views.getUsers, name="users"),
    path(
        "users/login/",
        profile_views.MyTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("users/register/", profile_views.registerUser.as_view(), name="register"),
    path("users/delete/", profile_views.deleteUser.as_view(), name="delete"),
    path("", include(router.urls)),
]
