from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from pandas_highcharts.core import serialize
from scap.api import generate_fcc_fields, generate_geodjango_objects, generate_from_lambda
# from scap.forms import LoginForm
from scap.generate_files import generate_fc_file, generate_fcc_file
from scap.utils import mask_with_tif
import pandas as pd
from django.contrib.auth import authenticate, login, logout
from scap.models import ForestCoverSource,AGBSource, Emissions
from ScapTestProject import settings

def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect("homepage")


# from scap.utils import test_py, test_method


# A test URL to test the methods@csrf_exempt
def test(req):
    # test_method()
    # generate_from_lambda()
    # mask_with_tif()
    # generate_fcc_file(req)
    # generate_fcc_fields("Mapbiomas", 2001)
    # return HttpResponse("The fields were generated. Please check http://127.0.0.1:8000/admin/scap/forestcoverchange/")
    generate_geodjango_objects()
    # generate_fc_file(req)


def home(request):
    return render(request, 'scap/index.html')


def peru(request):
    colors = []

    with open(settings.STATIC_ROOT + '\\data\\palette.txt') as f:
        for line in f:
            row = line.strip()
            temp = {}
            temp['LC'] = int(row.split(',')[0][2:])
            temp['AGB'] = int(row.split(',')[1][3:])
            temp['color'] = row.split(',')[2]
            colors.append(temp)

    df_lc = pd.DataFrame(list(ForestCoverSource.objects.all().values('id','fcs_name', 'fcs_color').order_by(
        'id')))  # Get the LC dataset data sorted by lc_id
    lcs = df_lc.to_dict('records')  # Convert the LC list to a dictionary
    df_agb = pd.DataFrame(list(AGBSource.objects.all().values('agb_id', 'agb_name')))  # Get the AGB dataset data
    agbs = df_agb.to_dict('records')  # Convert the AGB list to a dictionary
    df = pd.DataFrame(list(Emissions.objects.all().values()))  # Get the Emissions dataset data
    print(df["lc_id_id"])
    df["lc_id_id"] = "LC" + df["lc_id_id"].apply(str) # Add the prefix LC to the LC id column
    print(df["lc_id_id"])
    df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
    grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()

    # Pivot the data to get the data in the format required by the chart
    pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'], index='year',
                                 fill_value=None)
    # Serialize the data to json
    chart = serialize(pivot_table, render_to='container', output_type='json', type='spline', title='Emissions')
    # Return the home.html template with the chart data and the LC and AGB data
    return render(request, 'scap/pilotcountry1.html', context={'chart': chart, 'lcs': lcs, 'agbs': agbs,'colors':colors})

def thailand(request):
    return render(request, 'scap/pilotcountry2.html')


def aoi(request):
    return render(request, 'scap/aoi.html')


def addData(request):
    return render(request, 'scap/addData.html')
