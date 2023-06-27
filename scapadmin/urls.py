from django.urls import path

import scapadmin.views as views
from scapadmin import getData

urlpatterns = [
    path('', views.home, name='home'),
    path('get-series/', getData.chart, name='get-series'),
    path('emissions/', views.home, name='emissions'),
    path('deforestation/', views.deforestation, name='deforestation'),
    path('get-min-max/', getData.get_agg_check, name='get-min-max'),
]
