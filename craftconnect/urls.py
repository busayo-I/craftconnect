"""
URL configuration for craftconnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

# Health check root view
def home(request):
    return JsonResponse({"status": "ok", "message": "CraftConnect API is running"})

schema_view = get_schema_view(
    openapi.Info(
        title="CraftConnect API",
        default_version='v1',
        description="API documentation for CraftConnect Backend",
        contact=openapi.Contact(email="teamcraftconnect@gmail.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', home, name="home"),  # 👈 FIXED: root URL

    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/assessment/', include('assessments.urls')),
    path("api/jobs/", include("jobs.urls")),


    # Swagger documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)