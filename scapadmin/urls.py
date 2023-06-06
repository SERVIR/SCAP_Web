from django.conf.urls.static import static
from django.urls import path

import scapadmin.views as views
from SCAP_WebApp import settings
from scapadmin import getData

urlpatterns = [
    path('', views.home, name='home'),
    path('get-series/', getData.chart, name='get-series'),
]
