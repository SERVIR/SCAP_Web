from django.http import JsonResponse

from scapadmin.models import LC,AGB,Value,Predefined_AOI


def chart(request):
    result = Value.objects.all().order_by('year')
    data=list(result.values_list('year').distinct())

    years=[]
    final =[]
    for x in range(len(data)):
        years.append(data[x][0])
    for x in range(len(years)):
        data=list(result.values_list('lc_agb_value').filter(year=years[x]))
        d=[]
        for i in range(len(data)):
            d.append(data[i][0])
        if len(d)<len(years):
            x=len(years)-len(d)
            for i in range(x):
                d.append(None)

        final.append({'data':d,'name':"test"})

    return JsonResponse({"final":final}, safe=False)
