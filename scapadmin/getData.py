from django.http import JsonResponse

from scapadmin.models import LC,AGB,Value,Predefined_AOI


def chart(request):
    result = Value.objects.all().order_by('year')
    data=list(result.values_list('lc_agb_value','year','lc_id','agb_id'))
    print(len(data))
    return JsonResponse(data, safe=False)
