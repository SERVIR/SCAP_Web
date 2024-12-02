from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from scap.models import (AOIFeature, AOICollection, ForestCoverCollection, AGBCollection, CurrentTask,
                         ForestCoverStatistic, CarbonStatistic, ForestCoverFile, PilotCountry, CarbonStockFile, EmissionFile,UserMessage,AGBFile)

from django.contrib import admin
from django.contrib.gis.geos import GEOSGeometry

import scap.api as api
import scap.processing as processing

import geopandas as gpd
import logging
import shutil
import os

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

logger = logging.getLogger("django")

@admin.action(description="Load uploaded boundary shapefile to geometry field")
def load_boundary_geometry(modeladmin, request, queryset):
    for instance in queryset:
        boundary_file = instance.boundary_file
        if not boundary_file:
            logger.error('Attempted to load non-existent boundary file.')

        bf_path = boundary_file.path
        if not os.path.isfile(bf_path):
            logger.error('Boundary file field is not a valid file.')

        dir_path, ext = os.path.splitext(bf_path)
        if ext != '.zip':
            logger.error('Boundary file is not a .zip file.')

        if os.path.isdir(dir_path):
            logger.info('Deleting previous directory with same name as zip file')
            shutil.rmtree(dir_path)

        os.makedirs(dir_path)
        processing.unzip(bf_path, dir_path)
        shp_path = processing.get_shp_file(dir_path)
        if not shp_path:
            logger.error('No .shp file exists in .zip file')

        boundary_gdf = gpd.read_file(shp_path)
        union_geom = boundary_gdf.geometry.union_all()

        if isinstance(union_geom, Polygon):
            union_geom = MultiPolygon([union_geom])

        geom = GEOSGeometry(union_geom.wkt)

        instance.geom = geom
        instance.save()

class AOIFeatureAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','orig_name','iso3','desig_eng')
    list_filter = ('iso3','desig_eng')
    search_fields = ['name']


class CurrentTaskAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id','stage_progress')


class PilotCountryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('country_name','region','country_code','year_added','latitude','longitude','zoom_level')
    list_display_links = ('country_name',)


class ForestCoverFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'collection', 'file','validation_status')
    list_filter = ('collection',)


class AOICollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','owner','access_level')

class AGBCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','owner','access_level')
    actions = [load_boundary_geometry]


class ForestCoverFileInline(admin.TabularInline):
    model = ForestCoverFile
    show_change_link = True
    extra = 0


class ForestCoverCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'boundary_file','owner','access_level','approval_status')
    inlines = [ ForestCoverFileInline, ]
    actions = [load_boundary_geometry]


class CarbonStocksAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'agb_index', 'year_index', 'min', 'max')
    list_filter = ('fc_index', 'agb_index', 'year_index')
class AGBAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'agb_index', 'year_index', 'min', 'max')
    list_filter = ( 'agb_index', 'year_index')


class EmissionsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'agb_index', 'year_index', 'min', 'max')
    list_filter = ('fc_index', 'agb_index', 'year_index')


class CarbonStatisticsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'agb_index', 'aoi_index', 'year_index',
                    'final_carbon_stock', 'emissions', 'agb_value')
    list_filter = ('fc_index', 'agb_index', 'year_index')


class ForestCoverStatisticsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'aoi_index', 'year_index', 'final_forest_area', 'forest_gain', 'forest_loss')
    list_filter = ('fc_index', 'aoi_index', 'year_index')

class UserMessageAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('name', 'role', 'message')
    list_filter = ('name', 'role', 'message')

admin.site.register(PilotCountry, PilotCountryAdmin)

admin.site.register(AOICollection, AOICollectionAdmin)
admin.site.register(AGBCollection, AGBCollectionAdmin)
admin.site.register(ForestCoverCollection, ForestCoverCollectionAdmin)

admin.site.register(ForestCoverFile, ForestCoverFileAdmin)
admin.site.register(AOIFeature, AOIFeatureAdmin)

admin.site.register(CarbonStockFile, CarbonStocksAdmin)
admin.site.register(EmissionFile, EmissionsAdmin)
admin.site.register(AGBFile, AGBAdmin)
admin.site.register(UserMessage,UserMessageAdmin)

admin.site.register(ForestCoverStatistic, ForestCoverStatisticsAdmin)
admin.site.register(CarbonStatistic, CarbonStatisticsAdmin)

admin.site.register(CurrentTask, CurrentTaskAdmin)
