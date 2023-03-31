from service.settings import EMAIL_HOST_USER
from django.core.mail import EmailMessage
from api import models
import os


def send_report_email(reported_profile):
    # get photos
    reported_profile_photos = models.Photo.objects.filter(
        profile=reported_profile.id
    ).order_by("created_at")

    # email headers
    subject, from_email, to = (
        "Toogether Profile Report",
        EMAIL_HOST_USER,
        ["damianstonedev@gmail.com", "c3a.chris@gmail.com"],
    )

    # email content
    html_content = f"""
            <h1>Profile Reported</h1>
            <h3>The following profile has been reported</h3>

            <h3>Reported profile data:</h3>
            <ul>
                <li>Profile id: <strong>{reported_profile.id}<strong></li>
                <li>Profile name: <strong>{reported_profile.name}</strong></li>
                <li>Profile description: <strong>{reported_profile.description}</strong></li>
            </ul>
        """

    msg = EmailMessage(subject=subject, body=html_content, from_email=from_email, to=to)
    msg.content_subtype = "html"

    # attach all profile photos to email
    for photo in reported_profile_photos:
        # get filename and ext
        filename, ext = os.path.splitext(photo.image.name)

        # get file type
        file_type = ext.lower()[1:]

        # attach image to email
        with open(photo.image.path, "rb") as f:
            msg.attach(filename, f.read(), f"image/{file_type}")

    # send email
    msg.send()
