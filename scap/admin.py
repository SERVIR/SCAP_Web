from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from scap.models import (PredefinedAOI, BoundaryFiles, AOI, ForestCoverChange, AGBSource, ForestCoverSource, Emissions,
                         ForestCoverChangeFile, ForestCoverFile, UserProvidedAOI, NewCollection)


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
    list_filter = ('fc_source', 'year')


class ForestCoverChangeFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        'id', 'fc_source', 'baseline_year', 'year', 'created', 'processing_time', 'file_name', 'file_directory')
    list_filter = ('fc_source', 'created')


class ForestCoverFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_source', 'file_name', 'file_directory', 'created')
    list_filter = ('fc_source', 'created')


class UserProvidedAOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('aoi_name', 'path_to_aoi_file', 'last_accessed_on')


class NewCollectionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('collection_name', 'boundary_file', 'tiff_file', 'projection', 'resolution', 'last_accessed_on')


# admin.site.register(PredefinedAOI, PredefinedAOIAdmin)
class AGBSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('agb_id', 'agb_label', 'agb_name')
    list_display_links = ('agb_id', 'agb_label')


class ForestCoverSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('fcs_name', 'fcs_color', 'fcs_description', 'fcs_metadata', 'private')


class EmissionsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'agb_id', 'aoi_id', 'year', 'lc_agb_value')
    list_filter = ('lc_id', 'agb_id', 'year')


admin.site.register(AOI, AOIAdmin)
admin.site.register(UserProvidedAOI, UserProvidedAOIAdmin)
admin.site.register(NewCollection, NewCollectionAdmin)
admin.site.register(ForestCoverChange, ForestCoverChangeAdmin)
admin.site.register(ForestCoverChangeFile, ForestCoverChangeFileAdmin)
admin.site.register(BoundaryFiles, BoundaryFilesAdmin)
admin.site.register(ForestCoverFile, ForestCoverFileAdmin)
admin.site.register(AGBSource, AGBSourceAdmin)
admin.site.register(ForestCoverSource, ForestCoverSourceAdmin)
admin.site.register(Emissions, EmissionsAdmin)
