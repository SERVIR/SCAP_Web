from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
# Register your models here.

from .models import AGB, LC, Predefined_AOI, Emissions


class AGBAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('agb_id', 'agb_name')

class LCAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('lc_id', 'lc_name')

class Predefined_AOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('aoi_id', 'aoi_name', 'aoi_country')

class EmissionsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'agb_id', 'aoi_id','year', 'lc_agb_value')
    list_filter = ('lc_id', 'agb_id', 'year')

admin.site.register(AGB, AGBAdmin)
admin.site.register(LC, LCAdmin)
admin.site.register(Predefined_AOI, Predefined_AOIAdmin)
admin.site.register(Emissions, EmissionsAdmin)


