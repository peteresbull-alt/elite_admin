
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "SMSureConnect Administration"
admin.site.site_title = "SMSureConnect Admin Portal"
admin.site.index_title = "Welcome to SMSureConnect Admin Portal"


def home(request):
    return redirect("/admin")

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("app.urls")),
    path('', home, name="home"),
]

# Add this for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
