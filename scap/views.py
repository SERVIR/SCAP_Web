import numpy as np
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from pandas_highcharts.core import serialize
from scap.api import generate_fcc_fields, generate_geodjango_objects_aoi, generate_from_lambda, \
    generate_geodjango_objects_boundary
from scap.generate_files import generate_fc_file, generate_fcc_file
from scap.utils import mask_with_tif
import pandas as pd
from django.contrib.auth import authenticate, login, logout
from scap.models import ForestCoverSource, AGBSource, Emissions, ForestCoverChange, BoundaryFiles
from ScapTestProject import settings
import json


# A test URL to test the methods
@csrf_exempt
def test(req):
    try:
        # test_method()
        # generate_from_lambda()
        # mask_with_tif()
        # generate_fcc_file(req)
        generate_fcc_fields("CCI", 2002)
        # generate_geodjango_objects_aoi()
        # generate_geodjango_objects_boundary()
        # generate_fc_file(req)
        return HttpResponse("The script ran successfully")
    except Exception as e:
        return HttpResponse(str(e))


def home(request):
    return render(request, 'scap/index.html')

def map(request):
    return render(request, 'scap/map.html')

# This page shows when someone clicks on 'Peru' tile in home page
def peru(request):
    try:
        colors = []
        # generating list of colors from  the text file
        with open(settings.STATIC_ROOT + '/data/palette.txt') as f:
            for line in f:
                row = line.strip()
                temp = {}
                temp['LC'] = int(row.split(',')[0][2:])
                temp['AGB'] = int(row.split(',')[1][3:])
                temp['color'] = row.split(',')[2]
                colors.append(temp)

        # generating highcharts chart object from python using pandas(emissions chart)
        df_lc = pd.DataFrame(list(ForestCoverSource.objects.all().values('id', 'fcs_name', 'fcs_color').order_by(
            'id')))
        lcs = df_lc.to_dict('records')
        df_agb = pd.DataFrame(list(AGBSource.objects.all().values('agb_id', 'agb_name')))  # Get the AGB dataset data
        agbs = df_agb.to_dict('records')
        df = pd.DataFrame(list(Emissions.objects.all().values()))
        df["lc_id_id"] = "LC" + df["lc_id_id"].apply(str)
        df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
        grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()
        pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'],
                                     index='year',
                                     fill_value=None)
        chart = serialize(pivot_table, render_to='container', output_type='json', type='spline', title='Emissions')

        # generating highcharts chart object from python using pandas(forest cover change chart)
        df_defor = pd.DataFrame(
            list(ForestCoverChange.objects.filter(aoi__name='peru').values()))  # Get the ForestCoverChange dataset data
        df_lc_defor = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es').order_by(
            'id')))
        lcs_defor = df_lc_defor.to_dict('records')
        df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
        df_defor["nfc"] = df_defor['forest_gain'] - df_defor['forest_loss']
        years_defor = list(df_defor['year'].unique())
        pivot_table_defor = pd.pivot_table(df_defor, values='nfc', columns=['fc_source_id'],
                                           index='year', fill_value=None)
        chart_fc = serialize(pivot_table_defor, render_to='container1', output_type='json', type='spline',
                             xticks=years_defor,
                             title='Change in Forest Cover: Peru', )
        return render(request, 'scap/pilotcountry_peru.html',
                      context={'chart': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fc': chart_fc,
                               'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor})
    except Exception as e:
        return render(request, 'scap/pilotcountry_peru.html', {})


def thailand(request):
    return render(request, 'scap/pilotcountry2.html')


def aoi(request):
    return render(request, 'scap/aoi.html')


def protected_aois(request):
    try:
        pa_name = "Historic Sanctuary of Machu Picchu"
        colors = []
        # generating list of colors from  the text file
        with open(settings.STATIC_ROOT + '\\data\\palette.txt') as f:
            for line in f:
                row = line.strip()
                temp = {}
                temp['LC'] = int(row.split(',')[0][2:])
                temp['AGB'] = int(row.split(',')[1][3:])
                temp['color'] = row.split(',')[2]
                colors.append(temp)

        # generating highcharts chart object from python using pandas(emissions chart)
        df_lc = pd.DataFrame(list(ForestCoverSource.objects.all().values('id', 'fcs_name', 'fcs_color').order_by(
            'id')))
        lcs = df_lc.to_dict('records')
        df_agb = pd.DataFrame(list(AGBSource.objects.all().values('agb_id', 'agb_name')))  # Get the AGB dataset data
        agbs = df_agb.to_dict('records')
        df = pd.DataFrame(list(Emissions.objects.all().values()))
        df["lc_id_id"] = "LC" + df["lc_id_id"].apply(str)
        df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
        grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()
        pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'],
                                     index='year',
                                     fill_value=None)
        chart = serialize(pivot_table, render_to='emissions_chart_pa', output_type='json', type='spline',
                          title='Emissions: ' + pa_name)

        # generating highcharts chart object from python using pandas(forest cover change chart)
        df_defor = pd.DataFrame(list(ForestCoverChange.objects.filter(aoi__name=pa_name).values()))
        df_lc_defor = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es').order_by(
            'id')))
        lcs_defor = df_lc_defor.to_dict('records')
        df_defor["NFC"] = df_defor['forest_gain'] - df_defor['forest_loss']
        df_defor["TotalArea"]=df_defor["initial_forest_area"] + df_defor["NFC"]
        df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
        years_defor = list(df_defor['year'].unique())

        pivot_table_defor1 = pd.pivot_table(df_defor, values=['NFC','TotalArea'], columns=['fc_source_id'],
                                           index='year', fill_value=None)
        pivot_table_defor2 = pd.pivot_table(df_defor, values=['TotalArea'], columns=['fc_source_id'],
                                           index='year', fill_value=None)
        chart_fc1 = serialize(pivot_table_defor1, render_to='container_fcpa', output_type='json', type='spline',
                             xticks=years_defor,
                             title="Protected Area: " + pa_name,secondary_y=['TotalArea'])
        chart_fc2 = serialize(pivot_table_defor2, render_to='container_fcpa_hide', output_type='json', type='spline',
                             xticks=years_defor,
                             title="Protected Area: " + pa_name )

        return render(request, 'scap/protected_aois.html',
                      context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                               'chart_fcpa_hide': chart_fc2,'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor})
    except Exception as e:
        return render(request, 'scap/protected_aois.html')


def addData(request):
    return render(request, 'scap/addData.html')

def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect("homepage")
