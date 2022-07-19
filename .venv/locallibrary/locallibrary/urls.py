"""locallibrary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django import views
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers, serializers, viewsets
from django.contrib.auth.models import User
from catalog.views import ApptView
from catalog.models import ApiUser
#from catalog.models import ApiUser


urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += [
    path('catalog/', include('catalog.urls')),
]

urlpatterns += [
    path('', RedirectView.as_view(url='catalog/', permanent=True)),
]

urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ApiUser
        fields = ['url', 'username', 'email', 'is_staff']

class UserViewSet(viewsets.ViewSet):
    queryset = ApiUser.objects.all()
    serializer_class = UserSerializer


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'appts', ApptView, 'appts')

urlpatterns += [
    path('api/', include(router.urls)),
    path('api-auth', include('rest_framework.urls', namespace='restframework')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

