from django.http import JsonResponse
from nested_lookup import nested_lookup
from scapadmin.models import LC, AGB, Value, Predefined_AOI
from array import *
from SCAP_WebApp import settings

colors = []
with open(settings.STATIC_ROOT + '\data\palette.txt') as f:
    for line in f:
        row = line.strip()
        temp={}
        temp['LC'] = int(row.split(',')[0][2:])
        temp['AGB'] = int(row.split(',')[1][3:])
        temp['color'] = row.split(',')[2]
        colors.append(temp)


def getColor(lc, agb):
    for x in colors:
        if x['LC'] == lc and x['AGB'] == agb:
            return x['color']


def findkeys(node, kv):
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
                yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x


def chart(request):
    result = Value.objects.all().order_by('year')
    data = list(result.values_list('year').distinct())

    years = []
    final = []
    lcs = []
    agbs = []
    for x in range(len(data)):
        years.append(data[x][0])
    data = list(LC.objects.all().values_list('lc_id').distinct())
    lc = len(data)
    for x in range(len(data)):
        lcs.append(data[x][0])
    data = list(AGB.objects.all().values_list('agb_id').distinct())
    agb = len(data)
    for x in range(len(data)):
        agbs.append(data[x][0])
    new_arr = []
    data = list(result.values_list('lc_agb_value', 'lc_id', 'agb_id', 'year').order_by('year'))
    for x in range(len(data)):
        new_arr.append([data[x][0], data[x][1], data[x][2], data[x][3]])
    temp = {}
    for m in range(lc * agb):
        for lc in lcs:
            for agb in agbs:
                for x in range(len(new_arr)):
                    if new_arr[x][1] == lc and new_arr[x][2] == agb:
                        for i in range(len(years)):
                            if new_arr[x][3] == years[i]:
                                temp[str(years[i]) + "_" + str(lc) + '_' + str(agb)] = new_arr[x][0]
                final.append(temp)
                temp = {}
        break
    a1 = []
    ss = []
    for x in range(len(years)):
        for lc in lcs:
            for agb in agbs:
                for x in range(len(years)):
                    ss.append(str(years[x]) + "_" + str(lc) + '_' + str(agb))
    t = {'data': [], 'name': "", 'years': years, 'color': 'black'}
    for i in range(len(ss)):
        g = nested_lookup(ss[i], final)
        if len(t['data']) == len(lcs) * len(agbs):
            a1.append(t)
            t = {'data': [], 'name': "", 'years': years,
                 'color': 'black'}
        else:
            if len(g) == 0:
                t['data'].append(None)
                t['name'] = 'LC' + ss[i].split('_')[1] + "_AGB" + ss[i].split('_')[2]

            else:
                t['data'].append(g[0])
                t['name'] = 'LC' + ss[i].split('_')[1] + "_AGB" + ss[i].split('_')[2]
                t['color'] = getColor(int(ss[i].split('_')[1]), int(ss[i].split('_')[2]))
    new_l = [i for n, i in enumerate(a1) if i not in a1[n + 1:]]
    return JsonResponse({"final": new_l}, safe=False)
