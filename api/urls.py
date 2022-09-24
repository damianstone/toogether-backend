from django.urls import path, include
from rest_framework import routers
from api.views import profile_views, group_views
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

urlpatterns = [
    path("token/", profile_views.getUsers, name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/", profile_views.getUsers, name="users"),
    path(
        "users/login/",
        profile_views.MyTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path("users/register/", profile_views.registerUser, name="register"),
    path("users/delete/", profile_views.deleteUser, name="delete"),
    path("", include(router.urls)),
]
