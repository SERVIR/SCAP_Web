from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from scap.models import (PredefinedAOI, BoundaryFiles, AOI, ForestCoverChange,
                         ForestCoverChangeFile, ForestCoverFile)


# # Register your models here.
# class PredefinedAOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
#     list_display = ('aoi_label', 'aoi_name', 'aoi_country')
#     list_display_links = ('aoi_label',)


class BoundaryFilesAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name_es',)
    list_display_links = ('name_es',)


class AOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name',)
    list_display_links = ('name',)


class ForestCoverChangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        'id', 'fc_source', 'year', 'baseline_year', 'aoi', 'initial_forest_area', 'forest_gain', 'forest_loss',
        'processing_time')
    list_filter = ('fc_source',)


class ForestCoverChangeFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        'id', 'fc_source', 'baseline_year', 'year', 'created', 'processing_time', 'file_name', 'file_directory')
    list_filter = ('fc_source', 'created')


class ForestCoverFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_source', 'file_name', 'file_directory', 'created')
    list_filter = ('fc_source', 'created')


# admin.site.register(PredefinedAOI, PredefinedAOIAdmin)
admin.site.register(AOI, AOIAdmin)
admin.site.register(ForestCoverChange, ForestCoverChangeAdmin)
admin.site.register(ForestCoverChangeFile, ForestCoverChangeFileAdmin)
admin.site.register(BoundaryFiles, BoundaryFilesAdmin)
admin.site.register(ForestCoverFile, ForestCoverFileAdmin)
