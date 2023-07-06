import json

import pandas as pd
from django.shortcuts import render
from pandas_highcharts.core import serialize

from scapadmin.models import Emissions, ForestCoverChange, LC, AGB


# The view that sends the data to the Emissions chart in home.html
def home(request):
    df_lc = pd.DataFrame(list(LC.objects.all().values('lc_id', 'lc_name', 'lc_color').order_by(
        'lc_id')))  # Get the LC dataset data sorted by lc_id
    lcs = df_lc.to_dict('records')  # Convert the LC list to a dictionary
    df_agb = pd.DataFrame(list(AGB.objects.all().values('agb_id', 'agb_name')))  # Get the AGB dataset data
    agbs = df_agb.to_dict('records')  # Convert the AGB list to a dictionary
    df = pd.DataFrame(list(Emissions.objects.all().values()))  # Get the Emissions dataset data
    df["lc_id_id"] = "LC" + df["lc_id_id"]  # Add the prefix LC to the LC id column
    df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
    grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()

    # Pivot the data to get the data in the format required by the chart
    pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'], index='year',
                                 fill_value=0)
    # Serialize the data to json
    chart = serialize(pivot_table, render_to='container', output_type='json', type='spline', title='Emissions')
    # Return the home.html template with the chart data and the LC and AGB data
    return render(request, 'scapadmin/home.html', context={'chart': chart, 'lcs': lcs, 'agbs': agbs})


# The view that sends the data to the Change in Forest Cover chart in deforestation.html
def deforestation(request):
    df = pd.DataFrame(list(ForestCoverChange.objects.all().values()))  # Get the ForestCoverChange dataset data
    df_lc = pd.DataFrame(list(LC.objects.all().values('lc_id', 'lc_name', 'lc_color').order_by(
        'lc_id')))  # Get the LC dataset data sorted by lc_id
    lcs = df_lc.to_dict('records')  # Convert the LC list to a dictionary
    df["lc_id_id"] = "LC" + df["lc_id_id"]  # Add the prefix LC to the LC id column
    years = list(df['year'].unique())  # Get the unique years from the dataset
    # Get the data for the forest cover for each year
    pivot_table = pd.pivot_table(df, values=['forest_gain', 'forest_loss'], columns=['lc_id_id'], index='year',
                                 fill_value=0)
    # Serialize the data to json
    chart = serialize(pivot_table, render_to='container1', output_type='json', type='spline', xticks=years,
                      title='Change in Forest Cover', )
    return render(request, 'scapadmin/deforestation.html',
                  context={'chart': chart, 'lcs': json.dumps(lcs), 'lc_data': lcs})
