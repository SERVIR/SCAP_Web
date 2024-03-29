from django.db.models import Avg, Min, Max
from django.http import JsonResponse
#
from SCAP_WebApp import settings
from scapadmin.models import Emissions, ForestCoverSource, AGBSource
from django.views.decorators.csrf import csrf_exempt

def get_agg_check(request):
    result = Emissions.objects.all().order_by('year')
    data = list(result.values_list('year').distinct())
    years = []
    for x in range(len(data)):
        years.append(data[x][0])
    if request.method == 'POST':
        lcs = request.POST.getlist('lcs[]')
        agbs = request.POST.getlist('agbs[]')
        min_arr = []
        max_arr = []
        avg_arr = []
        data1 = list(
            Emissions.objects.filter(lc_id__in=lcs, agb_id__in=agbs).values('year').annotate(
                min=Min('lc_agb_value'), max=Max('lc_agb_value'), avg=Avg('lc_agb_value')))

        if len(data1) < 25:
            for y in years:
                if not any(d['year'] == y for d in data1):
                    data1.append({'year': y, 'min': None, 'max': None, 'avg': None})
                else:
                    pass
        data1.sort(key=lambda x: x['year'])
        print(data1)

        for x in range(len(data1)):
            min_arr.append(data1[x]['min'])
            max_arr.append(data1[x]['max'])
            avg_arr.append(data1[x]['avg'])

        return JsonResponse({"min": min_arr, "max": max_arr, "avg": avg_arr}, safe=False)


colors = []

with open(settings.STATIC_ROOT + '/data/palette.txt') as f:
    for line in f:
        row = line.strip()
        temp = {}
        temp['LC'] = int(row.split(',')[0][2:])
        temp['AGB'] = int(row.split(',')[1][3:])
        temp['color'] = row.split(',')[2]
        colors.append(temp)
#
def getColor(lc, agb):
    for x in colors:
        if x['LC'] == lc:
            if x['AGB'] == agb:
                return x['color']
#
#
# def findkeys(node, kv):
#     if isinstance(node, list):
#         for i in node:
#             for x in findkeys(i, kv):
#                 yield x
#     elif isinstance(node, dict):
#         if kv in node:
#             yield node[kv]
#         for j in node.values():
#             for x in findkeys(j, kv):
#                 yield x
#
#
def chart(request):
    result = Emissions.objects.all().order_by('year')
    data = list(result.values_list('year').distinct())

    years = []
    final = []
    lcs = []
    lcnames = []
    agbs = []
    agbnames = []
    for x in range(len(data)):
        years.append(data[x][0])
    print(years)
    data = list(Emissions.objects.order_by().values_list('lc_id', 'lc_id__fcs_name').distinct())
    lc = len(data)
    for x in range(len(data)):
        lcs.append(int(data[x][0]))
        lcnames.append(data[x][1] + ' (LC' + str(data[x][0]) + ')')
    data = list(Emissions.objects.order_by().values_list('agb_id', 'agb_id__agb_name').distinct())
    agb = len(data)
    for x in range(len(data)):
        agbs.append(int(data[x][0]))
        agbnames.append(data[x][1] + ' (AGB' + str(data[x][0]) + ')')
    lcs.sort()
    agbs.sort()
    new_arr = []
    data = list(result.values_list('lc_agb_value', 'lc_id', 'agb_id', 'year').order_by('year'))
    for x in range(len(data)):
        new_arr.append([data[x][0], str(data[x][1]), data[x][2], data[x][3]])
    temp = {}
    for m in range(lc * agb):
        for lc in lcs:
            for agb in agbs:
                for x in range(len(new_arr)):
                    if new_arr[x][1] == str(lc) and new_arr[x][2] == str(agb):
                        for i in range(len(years)):
                            if new_arr[x][3] == years[i]:
                                temp[str(years[i]) + "_" + str(lc) + '_' + str(agb)] = new_arr[x][0]
                final.append(temp)
                temp = {}
            print("LC" + str(lc) + " done")
        break
    a1 = [None] * len(final)
    ss = []
    for x in range(len(years)):
        for lc in lcs:
            for agb in agbs:
                for x in range(len(years)):
                    ss.append(str(years[x]) + "_" + str(lc) + '_' + str(agb))
    t = {'data': [], 'name': "", 'years': years, 'color': 'black'}
    for i in range(len(final)):
        print(list(final[i].keys()))
        t['name'] = 'LC' + list(final[i].keys())[0].split('_')[1] + "/AGB" + list(final[i].keys())[0].split('_')[2]
        print(t['name'])
        t['color'] = getColor(int(list(final[i].keys())[0].split('_')[1]),
                              int(list(final[i].keys())[0].split('_')[2]))
        t['years'] = years
        # print(final[i])
        for m in list(final[i].keys()):
            t['data'].append(final[i][m] if final[i][m]>0 else None)
        a1[i] = t
        t = {'data': [], 'name': "", 'years': years, 'color': 'black'}

    print(a1)

    new_l = [i for n, i in enumerate(a1) if i not in a1[n + 1:]]
    print(len(new_l))
    return JsonResponse({"final": new_l, "lcs": lcnames, "agbs": agbnames}, safe=False)
#
@csrf_exempt
def get_series_name(request):
    if request.method == 'POST':
        lc_id = request.POST.get('ds_lc')
        print(lc_id)
        agb_id = request.POST.get('ds_agb')
        ds = ForestCoverSource.objects.get(id=lc_id[2:])
        lc_name= ds.fcs_name
        if agb_id != "":
            ds= AGBSource.objects.get(agb_id=agb_id[3:])
            agb_name= ds.agb_name
        else:
            agb_name= ''
        return JsonResponse({"name": lc_name+', '+agb_name}, safe=False)