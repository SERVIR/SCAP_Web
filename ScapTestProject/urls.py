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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.auth import views as auth_views

from ScapTestProject import settings
from scap.validation import doi_valid

from scap.api import (save_forest_cover_file, is_forest_cover_collection_valid, get_forest_cover_collections,
                      updatetomodel, get_yearly_forest_cover_files, save_AOI, get_aoi_list, delete_AOI,
                      get_AOI, get_tiff_data, get_updated_series, get_series_name, get_agg_check,
                      stage_for_processing, delete_tiff_record, get_tiff_id, add_tiff_record, update_tiff_record,
                      get_aoi_id,add_aoi_data,add_agb_data,update_boundary_file,test,upload_drawn_aoi,send_message_scap,get_agg_check_cs,get_agg_check_cs_pa)

from scap.views import (home, protected_aois, map, pilot_country, updateColl, page_not_found_view, add_new_collection, \
                        ManageForestCoverCollections, ManageAOICollections, ManageAGBCollections, \
                        CreateForestCoverCollection, CreateAGBCollection, CreateAOICollection, \
                        DeleteForestCoverCollection, DeleteAOICollection, DeleteAGBCollection,
                        EditForestCoverCollection, EditAOICollection, EditAGBCollection)

urlpatterns = [
      path('', home, name='home'),
      path('', include("allauth.account.urls")),

      path('admin', RedirectView.as_view(url='admin/')),
      path('admin/', admin.site.urls),
      path("accounts/", include("django.contrib.auth.urls")),
      path('google-login/', include('allauth.urls')),
      path('login/', auth_views.LoginView.as_view(), name='login'),

      path('home/', home, name='home2'),
      path('pilot/<int:country>/', pilot_country, name='pilot_country'),
      path('map/<int:country>/', map, name='map'),
      path('map/', map, name='map'),
      path('aoi/<int:aoi>/', protected_aois, name='aoi_page'),
      path('contribute-data/', add_new_collection, name='contribute-data'),
      path('send-message-scap/',send_message_scap,name='send-message-scap'),

      path('get-series-name/', get_series_name, name='get-series-name'),
      path('aoi/<int:country>/get-min-max/', get_agg_check, name='get-min-max'),
      path('aoi/<int:country>/get-min-max-cs/', get_agg_check_cs_pa, name='get-min-max-cs-pa'),
      path('pilot/<int:country>/get-min-max/', get_agg_check, name='get-min-max'),
      path('pilot/<int:country>/get-min-max-cs/', get_agg_check_cs, name='get-min-max-cs'),
      path('pilot/<int:country>/get-series-name/', get_series_name, name='get_series_name'),

      path('map/get-aoi/', get_AOI, name='get-aoi'),
      path('map/<int:country>/upload-drawn-aoi/', upload_drawn_aoi, name='upload-drawn-aoi'),

      path('aoi/<int:country>/get-aoi/', get_AOI, name='get-aoi'),
      path('map/<int:country>/get-aoi-id/',get_aoi_id,name='get-aoi-id'),
      path('pilot/<int:country>/get-aoi-id/',get_aoi_id,name='get-aoi-id-pilot'),
      path('pilot/<int:country>/get-aoi/', get_AOI, name='get-aoi'),

      path('delete-aoi/', delete_AOI, name='delete-aoi'),
      path('save-aoi/', save_AOI, name='save-aoi'),

      path('save-forest-cover-file/', save_forest_cover_file, name='savetomodel'),
      path('get-forest-cover-collections/', get_forest_cover_collections, name='getcollections'),
      path('get-yearly-forest-cover-files/', get_yearly_forest_cover_files, name='get-yearly-forest-cover-files'),
      path('is-forest-cover-collection-valid/', is_forest_cover_collection_valid, name='is-forest-cover-collection-valid'),

      path('forest-cover-collections/', ManageForestCoverCollections.as_view(), name='forest-cover-collections'),
      path('forest-cover-collections/add/', CreateForestCoverCollection.as_view(), name='create-forest-cover-collection'),
      path('forest-cover-collections/edit/<int:pk>/', EditForestCoverCollection.as_view(), name='edit-forest-cover-collection'),
      path('forest-cover-collections/delete/<int:pk>/', DeleteForestCoverCollection.as_view(), name='delete-forest-cover-collection'),
      path('forest-cover-collections/edit/<int:pk>/update-boundary-file/',update_boundary_file,name='update-boundary-file'),

      path('aoi-collections/', ManageAOICollections.as_view(), name='aoi-collections'),
      path('aoi-collections/add/', CreateAOICollection.as_view(), name='create-aoi-collection'),
      path('aoi-collections/edit/<int:pk>/', EditAOICollection.as_view(), name='edit-aoi-collection'),
      path('aoi-collections/delete/<int:pk>/', DeleteAOICollection.as_view(), name='delete-aoi-collection'),
      path('aoi-collections/add/doi/', doi_valid, name='doi-valid'),
      path('aoi-collections/add/store-for-processing/', add_aoi_data, name='add-aoi-data'),
      path('aoi-collections/add/stage-for-processing/', stage_for_processing, name='stage-aoi-data'),

      path('agb-collections/', ManageAGBCollections.as_view(), name='agb-collections'),
      path('agb-collections/add/', CreateAGBCollection.as_view(), name='create-agb-collection'),
      path('agb-collections/edit/<int:pk>/', EditAGBCollection.as_view(), name='edit-agb-collection'),
      path('agb-collections/delete/<int:pk>/', DeleteAGBCollection.as_view(), name='delete-agb-collection'),
      path('agb-collections/add/doi/', doi_valid, name='doi-valid'),
      path('agb-collections/add/store-agb-for-processing/', add_agb_data, name='add-agb-data'),
      path('agb-collections/edit/<int:pk>/store-agb-for-processing/', add_agb_data, name='add-agb-data'),
      path('agb-collections/edit/<int:pk>/update-boundary-file/', update_boundary_file,
                         name='update-boundary-file'),

      path('forest-cover-collections/add/doi/', doi_valid, name='doi-valid'),
      path('forest-cover-collections/edit/<int:pk>/doi/', doi_valid, name='doi-valid-by-year'),
      path('forest-cover-collections/edit/<int:pk>/get-tiff-data/', get_tiff_data, name='doi-get-tiff-data'),
      path('forest-cover-collections/edit/<int:pk>/stage-for-processing/',stage_for_processing,name='stage-for-processing'),
      path('forest-cover-collections/edit/<int:pk>/delete-tiff-record/',delete_tiff_record,name='delete-tiff-record'),
      path('forest-cover-collections/edit/<int:pk>/get-tiff-id/', get_tiff_id, name='get-tiff-id'),
      path('forest-cover-collections/edit/<int:pk>/add-tiff-record/', add_tiff_record, name='add-tiff-record'),
      path('forest-cover-collections/edit/<int:pk>/update-tiff-record/', update_tiff_record, name='update-tiff-record'),


                    # STAGE FOR DELETION
      # path('get_aoi_list/', get_aoi_list, name='get_aoi_list'),
      path('test/', test, name='test'),
      # path('emissions/', pilot_country, name='emissions'),
      # path('update-coll/<str:coll_name>/', updateColl, name='update-coll'),
      # path('aoi/<str:country>/get-updated-series/', get_updated_series, name='get-updated-series'),
      # path('protected_areas/get-series-name/', get_series_name, name='get-series-name'),
      # path('protected_areas/', protected_aois, name='protected_aois'),
      # path('protected_areas/get-min-max/', get_agg_check, name='get-min-max'),
      # path('protected_areas/<str:country>/get-series-name/', get_series_name, name='get-series-name'),
      # path('updatetomodel/', updatetomodel, name='updatetomodel'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = page_not_found_view
