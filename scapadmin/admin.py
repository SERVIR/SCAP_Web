from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
# Register your models here.

from .models import AGB, LC, Predefined_AOI, Value


class AGBAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('agb_id',)

class LCAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('lc_id',)

class Predefined_AOIAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('aoi_id', 'aoi_name', 'aoi_country')

class ValueAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('id', 'lc_id', 'agb_id', 'year', 'lc_agb_value')
    list_filter = ('lc_id', 'agb_id', 'year')

admin.site.register(AGB, AGBAdmin)
admin.site.register(LC, LCAdmin)
admin.site.register(Predefined_AOI, Predefined_AOIAdmin)
admin.site.register(Value, ValueAdmin)


