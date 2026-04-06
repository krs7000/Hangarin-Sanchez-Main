from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [path("", include("hangarin.urls"))]

if settings.SOCIAL_LOGIN_ENABLED:
    urlpatterns.append(path("accounts/", include("allauth.urls")))

urlpatterns.append(path("", include("pwa.urls")))
urlpatterns.append(path("admin/", admin.site.urls))
