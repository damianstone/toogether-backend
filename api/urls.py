from django.urls import path, include
from rest_framework import routers
from api.views import profile_views as views
from rest_framework_simplejwt.views import (TokenRefreshView)


router = routers.DefaultRouter()

router.register(
    r"profiles",
    views.ProfileViewSet,
    basename="profile",
)

router.register(
    r"photos",
    views.PhotoViewSet,
    basename="photo",
)

urlpatterns = [
    path('token/', views.getUsers, name="token"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("users/", views.getUsers, name="users"),
    path(
        "users/login/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("users/register/", views.registerUser, name="register"),
    path("users/delete/", views.deleteUser, name="delete"),
    path("", include(router.urls)),
]
