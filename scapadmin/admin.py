from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import AGB, LC, Predefined_AOI, Emissions, ForestCoverChange


# Register your models here.

class AGBAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('agb_id', 'agb_label', 'agb_name')
    list_display_links = ('agb_id', 'agb_label')


class LCAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('lc_id', 'lc_label', 'lc_name')
    list_display_links = ('lc_id', 'lc_label')

class Predefined_AOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('aoi_id', 'aoi_label', 'aoi_name', 'aoi_country')
    list_display_links = ('aoi_id', 'aoi_label')


class EmissionsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'agb_id', 'aoi_id', 'year', 'lc_agb_value')
    list_filter = ('lc_id', 'agb_id', 'year')


class ForestCoverChangeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'aoi_id', 'year', 'forest_gain', 'forest_loss', 'initial_forest_area')
    list_filter = ('lc_id', 'year')


admin.site.register(AGB, AGBAdmin)
admin.site.register(LC, LCAdmin)
admin.site.register(Predefined_AOI, Predefined_AOIAdmin)
admin.site.register(Emissions, EmissionsAdmin)
admin.site.register(ForestCoverChange, ForestCoverChangeAdmin)
