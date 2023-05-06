from django.contrib.gis import admin
from .models import Profile, Photo, Group, Match, VerificationCode

# Register your models here.
admin.site.register(Profile, admin.OSMGeoAdmin)
admin.site.register(Photo, admin.OSMGeoAdmin)
admin.site.register(Match, admin.OSMGeoAdmin)
admin.site.register(Group, admin.OSMGeoAdmin)
admin.site.register(VerificationCode, admin.OSMGeoAdmin)
