from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from scap.models import (AOIFeature, AOICollection, ForestCoverCollection, AGBCollection,
                         ForestCoverStatistic, CarbonStatistic, ForestCoverFile, PilotCountry)


class AOIFeatureAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name','orig_name','iso3','desig_eng')
    list_filter = ('iso3','desig_eng')
    search_fields = ['name']



class PilotCountryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('country_name',)
    list_display_links = ('country_name',)


class ForestCoverFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'collection', 'file')
    list_filter = ('collection',)


class AOICollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name',)

class AGBCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name',)


class TiffFileInline(admin.StackedInline):
    model = ForestCoverFile


class ForestCoverCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name', 'boundary_file')
    inlines = [ TiffFileInline, ]


class CarbonStatisticsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'agb_index', 'aoi_index', 'year_index',
                    'initial_carbon_stock', 'emissions', 'agb_value')
    list_filter = ('fc_index', 'agb_index', 'year_index')


class ForestCoverStatisticsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_index', 'aoi_index', 'year_index', 'final_forest_area', 'forest_gain', 'forest_loss')
    list_filter = ('fc_index', 'aoi_index', 'year_index')



admin.site.register(PilotCountry, PilotCountryAdmin)

admin.site.register(AOICollection, AOICollectionAdmin)
admin.site.register(AGBCollection, AGBCollectionAdmin)
admin.site.register(ForestCoverCollection, ForestCoverCollectionAdmin)

admin.site.register(ForestCoverFile, ForestCoverFileAdmin)
admin.site.register(AOIFeature, AOIFeatureAdmin)

admin.site.register(ForestCoverStatistic, ForestCoverStatisticsAdmin)
admin.site.register(CarbonStatistic, CarbonStatisticsAdmin)
