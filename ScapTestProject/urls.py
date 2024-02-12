"""ScapTestProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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

from scap.api import savetomodel, check_if_coll_exists, getcollections, updatetomodel, getfilesfromcollection, \
    saveAOItomodel, get_aoi_list, delete_AOI
from scap.views import test, home, aoi, peru, addData, thailand, protected_aois, map
from django.contrib.auth import views as auth_views
from scap import getData

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('home/', home, name='home2'),
    path("", include("allauth.account.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path('savetomodel/', savetomodel, name='savetomodel'),
    path('test/', test, name='test'),
    path('google-login/', include('allauth.urls')),
    path('getcollections/', getcollections, name='getcollections'),
    path('getfilesfromcollection/', getfilesfromcollection, name='getfilesfromcollection'),
    path('delete_AOI/', delete_AOI, name='delete_AOI'),
    path('saveAOItomodel/', saveAOItomodel, name='saveAOItomodel'),
    path('updatetomodel/', updatetomodel, name='updatetomodel'),
    path('check_if_coll_exists/', check_if_coll_exists, name='check_if_coll_exists'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('get_aoi_list/', get_aoi_list, name='get_aoi_list'),
    path('aoi', aoi, name='aoi'),
    path('peru/', peru, name='peru'),
    path('protected_aois/', protected_aois, name='protected_aois'),
    path('thailand/', thailand, name='thailand'),
    path('addData/', addData, name='addData'),
    path('get-series/', getData.chart, name='get-series'),
    path('emissions/', peru, name='emissions'),
    # path('deforestation/', views.deforestation, name='deforestation'),
    path('peru/get-min-max/', getData.get_agg_check, name='get-min-max'),
    path('peru/get-series-name/', getData.get_series_name, name='get-series-name'),
    path('protected_aois/get-min-max/', getData.get_agg_check, name='get-min-max'),
    path('protected_aois/get-series-name/', getData.get_series_name, name='get-series-name'),
    path('get-series-name/', getData.get_series_name, name='get-series-name'),
    path('map/', map, name='map')
    #
]
