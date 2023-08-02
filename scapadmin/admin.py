from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

# Register your models here.
from scapadmin.models import AGBSource, PredefinedAOI, ForestCoverChangeFile, \
    ForestCoverFile, ForestCoverSource, Emissions, ForestCoverChange


class AGBSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('agb_id', 'agb_label', 'agb_name')
    list_display_links = ('agb_id', 'agb_label')


class ForestCoverSourceAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('fcs_name', 'fcs_color', 'fcs_description','fcs_metadata','private')


class PredefinedAOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ( 'aoi_label', 'aoi_name', 'aoi_country')
    list_display_links = ('aoi_label',)


class EmissionsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'agb_id', 'aoi_id', 'year', 'lc_agb_value')
    list_filter = ('lc_id', 'agb_id', 'year')

#
class ForestCoverChangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_source', 'aoi')
    list_filter = ('fc_source',)


class ForestCoverChangeFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_source', 'baseline_year', 'year', 'created', 'processing_time', 'file_name', 'file_directory')
    list_filter = ('fc_source', 'created')


class ForestCoverFileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'fc_source', 'file_name', 'file_directory', 'created')
    list_filter = ('fc_source', 'created')


admin.site.register(AGBSource, AGBSourceAdmin)
admin.site.register(ForestCoverSource, ForestCoverSourceAdmin)
admin.site.register(PredefinedAOI, PredefinedAOIAdmin)
admin.site.register(Emissions, EmissionsAdmin)
admin.site.register(ForestCoverChange, ForestCoverChangeAdmin)
admin.site.register(ForestCoverChangeFile, ForestCoverChangeFileAdmin)
admin.site.register(ForestCoverFile, ForestCoverFileAdmin)

