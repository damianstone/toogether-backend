from rest_framework import status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django.core.exceptions import ObjectDoesNotExist
from api import models, serializers
from django.conf import settings

import random
from datetime import date, timedelta
from faker import Faker

from api.data.cities import cities

# * List profiles
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_profiles(request):
    profiles = models.Profile.objects.all()
    serializer = serializers.ProfileSerializer(profiles, many=True)
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )


# * Remove any profile by id
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_profile(request, pk=None):
    try:
        profile_to_delete = models.Profile.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(
            {"detail": "Object does not exist"}, status=status.HTTP_400_BAD_REQUEST
        )

    profile_to_delete.delete()
    return Response({"detail": "success"}, status=status.HTTP_200_OK)


# * Create 200 fake profiles
@api_view(["POST"])
@permission_classes([IsAdminUser])
def generated_profiles(request):
    current_user = request.user

    if not settings.DEBUG:
        return Response(
            {"error": "This action cannot be performed in production"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    
    # TODO: check if there are more than 100 profiles 

    # initialize Faker generator
    fake = Faker("en_GB")

    # generate 200 fake profiles
    for i in range(200):
        # generate first and last name
        first_name = fake.first_name()
        last_name = fake.last_name()

        # generate name
        name = f"{first_name} {last_name}"

        # generate Instagram username from name and last name
        instagram = f"{first_name.lower()}.{last_name.lower()}"

        # generate email
        email = f"{first_name.lower()}{last_name.lower()}@gmail.com"

        # generate age between 5 years less and more than the age of the current user
        current_age = current_user.age
        age = fake.random_int(current_age - 5, current_age + 5)

        # generate a random birthdate (yyyy-mm-dd) using the age
        birthdate = date.today() - timedelta(days=age * 365)
        birthdate_str = birthdate.strftime("%Y-%m-%d")

        # generate gender opposite of the current user
        gender = "M" if current_user.gender == "W" else "W"

        # location
        location = current_user.location

        # city
        city = random.choice(cities)

        # generate random sentences
        num_sentences = random.randint(7, 10)
        sentences = fake.sentences(num_sentences)

        # join sentences into a single paragraph
        description = " ".join(sentences)

        # create profile with generated data
        profile = models.Profile.objects.create(
            has_account=True,
            name=name,
            email=email,
            location=location,
            birthdate=birthdate_str,
            age=age,
            gender=gender,
            show_me="X",
            city=city,
            nationality="British",
            instagram=instagram,
            description=description,
            university=f"University of {city}",
        )
        profile.save()

    profiles = models.Profile.objects.all()
    serializer = serializers.ProfileSerializer(profiles, many=True)
    return Response(
        {"count": len(serializer.data), "results": serializer.data},
        status=status.HTTP_200_OK,
    )


# * Delete all the profiles except you (the admin)
@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_all_profiles(request, pk=None):
    current_user = request.user
    profiles = models.Profile.objects.exclude(id=current_user.id)

    if not settings.DEBUG:
        return Response(
            {"error": "This action cannot be performed in production"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    for profile in profiles:
        profile.delete()

    return Response(
        {"detail": f"sucess, {len(profiles)} profiles removed"},
        status=status.HTTP_200_OK,
    )
