from django.urls import path
from api.views import profile_views as views

urlpatterns = [
    # ---------------------USER---------------------
    path("login/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # register / create new user
    path("register/", views.registerUser, name="register"),
    # register / create new user
    path("delete/<str:pk>/", views.deleteUser, name="delete"),
    # get the users profiles with the django fields
    path("", views.getUsers, name="users"),
    
    # ---------------------PROFILE---------------------
    # get all profiles
    path("profiles/", views.getProfiles, name="get-profiles"),
    # get profile by id
    path("profiles/profile/<str:pk>/", views.getProfile, name="get-profile"),
    # create profile
    path("profiles/profile/<str:pk>/create-profile/", views.createProfile, name="profile-create"),
    # update profile
    path("profiles/profile/<str:pk>/update-profile/", views.updateProfile, name="profile-create"),
    
    # ---------------------PHOTO---------------------
    # add photo/s
    path("profiles/upload/", views.addPhoto, name="add-photo"),
    # get profile photos
    path("profiles/photos/", views.getProfilePhotos, name="get-profile-photos"),
    # get all the photos (admin)
    path("profiles/photos/", views.getPhotos, name="get-all-photos"),
    # delete photo
    path("profiles/photos/<str:pk>/", views.deletePhoto, name="delete-photos"),
    
    # ---------------------BLOCKED USERS---------------------
    # block profile
    path("profiles/block-profile/", views.blockProfile, name="block-profile"),
    # block profile
    path("profiles/disblock-profile/", views.disblockProfile, name="disblock-profile"),
    # get blocked profiles
    path(
        "profiles/profile/<str:pk>/blocked-profiles/",
        views.getBlockedProfiles,
        name="get-blocked-profiles",
    ),
]
