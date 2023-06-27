# Create your views here.
from django.shortcuts import render

from scapadmin.models import Emissions, ForestCoverChange, LC, AGB
import pandas as pd
from pandas_highcharts.core import serialize


def home(request):
    df_lc = pd.DataFrame(list(LC.objects.all().values('lc_id', 'lc_name')))
    lcs=df_lc.to_dict('records')

    df_agb = pd.DataFrame(list(AGB.objects.all().values('agb_id', 'agb_name')))
    agbs=df_agb.to_dict('records')

    df = pd.DataFrame(list(Emissions.objects.all().values()))
    df["lc_id_id"] = "LC" + df["lc_id_id"]
    df["agb_id_id"] = "AGB" + df["agb_id_id"]

    grouped_data = df.groupby(['year','lc_id_id','agb_id_id'])['lc_agb_value'].sum().reset_index()
    # Create a pivot table with years as columns, lcs and agbs as rows, and sales as values

    pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'], index='year',
                                 fill_value=0)

    chart = serialize(pivot_table, render_to='container', output_type='json',type='spline', title='Emissions')

    return render(request, 'scapadmin/home.html', context={'chart': chart,'lcs':lcs,'agbs':agbs})


def deforestation(request):
    df = pd.DataFrame(list(ForestCoverChange.objects.all().values()))
    df_lc = pd.DataFrame(list(LC.objects.all().values('lc_id', 'lc_name')))
    lcs = df_lc.to_dict('records')
    df["lc_id_id"] = "LC" + df["lc_id_id"]
    years= list(df['year'].unique())
    pivot_table = pd.pivot_table(df, values= ['forest_gain','forest_loss'], columns=['lc_id_id'], index='year',
                                 fill_value=0)
    chart = serialize(pivot_table, render_to='container1', output_type='json',type='spline', xticks=years, title='Change in Forest Cover',)
    return render(request, 'scapadmin/deforestation.html', context={'chart': chart,'lcs':lcs})

