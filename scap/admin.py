from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from scap.models import (AOIFeature, AOICollection, ForestCoverCollection, AGBCollection, CurrentTask,
                         ForestCoverStatistic, CarbonStatistic, ForestCoverFile, PilotCountry, CarbonStockFile, EmissionFile,UserMessage,AGBFile)


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
    list_display = ('id', 'collection', 'file')
    list_filter = ('collection',)


class AOICollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','owner','access_level')

class AGBCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','owner','access_level')


class ForestCoverFileInline(admin.TabularInline):
    model = ForestCoverFile
    show_change_link = True
    extra = 0


class ForestCoverCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'boundary_file','owner','access_level')
    inlines = [ ForestCoverFileInline, ]


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
