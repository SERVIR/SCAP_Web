import os
import json
import logging
import shapely
import pandas as pd
import geopandas as gpd


from datetime import datetime, date, timedelta
from pathlib import Path
from django.contrib import auth
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group

from ScapTestProject.celery import app as app
from scap.api import (fetch_forest_change_charts, fetch_forest_change_charts_by_aoi, fetch_carbon_charts,
                      fetch_carbon_stock_charts,
                      get_available_colors, generate_geodjango_objects_aoi, fetch_deforestation_charts,
                      fetch_deforestation_charts_by_aoi)
from scap.forms import ForestCoverCollectionForm, AOICollectionForm, AGBCollectionForm, UserRoleForm
from scap.models import (CarbonStatistic, ForestCoverFile, ForestCoverCollection, AOICollection, AGBCollection,
                         PilotCountry, AOIFeature, CurrentTask, ForestCoverStatistic)


from scap.async_tasks import process_updated_collection
from scap.getgdalstats import gdal_stats

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def map_cog(request, country=0):
    json_obj = {}
    fc_arr = []
    cs_arr = []
    fc_colls = []
    agb_colls = []
    zoom_level = 3  # global extent center
    lat_long = [44, 10]  # global extent center
    fc_collection = ForestCoverCollection.objects.filter(access_level='Public')
    for fc in fc_collection:
        fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
        fc_years = []
        for fc_yr in fc_files:
            fc_years.append(fc_yr['year'])
        fc_colls.append({'name': str(fc), 'years': fc_years})
    agb_collection = AGBCollection.objects.filter(access_level='Public').values()
    for agb in agb_collection:
        agb_colls.append({'name': agb['name'], 'years': [agb['year']]})
    pc = PilotCountry.objects.filter(id=country).values()
    default_lc = 'JAXA'
    default_agb = 'Saatchi 2000'
    if country > 0:
        pa = PilotCountry.objects.get(id=country)
        if pa.forest_cover_collection is not None:
            default_lc = pa.forest_cover_collection.name
            default_agb = pa.agb_collection.name
    for pilot in pc:
        zoom_level = pilot['zoom_level']
        lat_long = [pilot['latitude'], pilot['longitude']]
        break
    pilot_countries = PilotCountry.objects.all().order_by('country_name')

    try:
        if len(pc) > 0:
            aois = AOIFeature.objects.filter(iso3=pc[0]['country_code']).exclude(desig_eng='COUNTRY')
            aoi_arr = []
            for aoi in aois:
                aoi_geojson = json.loads(aoi.geom.geojson)
                aoi_geojson['properties'] = {'name': aoi.name, 'ISO3': aoi.iso3, 'desig_eng': aoi.desig_eng}

                aoi_arr.append(aoi_geojson)
            country_shp = AOIFeature.objects.filter(iso3=pc[0]['country_code'], desig_eng='COUNTRY').last()
            country_geojson = json.loads(country_shp.geom.geojson)
            country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                             'desig_eng': country_shp.desig_eng}
            json_obj["data_pa"] = aoi_arr
            country_geojson['coordinates'] = [
                [[[-179, 70],
                  [-179, -70],
                  [179, -70],
                  [179, 70],
                  [-179, 70]]] + country_geojson['coordinates'][0]]
            json_obj["data_country"] = [country_geojson]


        else:
            json_obj["data_pa"] = []
            json_obj["data_country"] = []
        lcs = []
        agbs = []
        if request.user.is_authenticated:
            df_lc_owner = ForestCoverCollection.objects.filter(owner=request.user).values()
            df_lc_public = ForestCoverCollection.objects.filter(access_level='Public').values()
            df_lc = pd.DataFrame((df_lc_owner.union(df_lc_public).values()))

            lcs = df_lc.to_dict('records')
            df_agb_owner = AGBCollection.objects.filter(owner=request.user).values()
            df_agb_public = AGBCollection.objects.filter(access_level='Public').values()
            df_agb = pd.DataFrame(df_agb_owner.union(df_agb_public).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        else:
            df_lc = pd.DataFrame(ForestCoverCollection.objects.filter(access_level='Public').values())
            lcs = df_lc.to_dict('records')
            df_agb = pd.DataFrame(
                AGBCollection.objects.filter(access_level='Public').values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')

    except Exception as e:
        print(e)
        json_obj["data_pa"] = []
        json_obj["data_country"] = []
    return render(request, 'scap/map_cog.html',
                  context={'shp_obj': json_obj, 'country_id': country, 'lcs': lcs, 'agbs': agbs,
                           'pilot_countries': pilot_countries,
                           'latitude': lat_long[0], 'longitude': lat_long[1],
                           'zoom_level': zoom_level, 'lat_long': lat_long, 'region': '', 'default_lc': default_lc,
                           'default_agb': default_agb,
                           'fc_colls': fc_colls, 'agb_colls': agb_colls})


def user_information(request):
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            other_explanation = form.cleaned_data.get('other_explanation', '')
            user = request.user
            # Fetch all users in the Approvers group
            approver_group = Group.objects.get(name='scap_sysadmins')
            approvers = approver_group.user_set.all()

            # Construct the email content
            subject = '[S-CAP] New User Registration'
            message = f"""


                       User Profile: <a href='https://s-cap.servirglobal.net/admin/auth/user/{user.id}/change/'>{user.id}</a>
                       Name: {user.get_full_name() or user.username}
                       Access Needed for : {role}
                       """
            if role == 'Other' and other_explanation:
                message += f"Other Explanation: {other_explanation}"

            # Send the email to all approvers
            approvers_emails = [approver.email for approver in approvers if approver.email]
            send_mail(subject, message, config['EMAIL_HOST_USER'], approvers_emails)

            # Redirect to home or another page after successful submission
            return redirect('home')
    else:
        form = UserRoleForm()

    return render(request, 'scap/user_information.html', {'form': form})


def test_stats(request):
    gdal_stats()
    return HttpResponse('done')


def home(request):
    is_new_user = request.session.get('is_new_user', False)
    if is_new_user:
        del request.session['is_new_user']
        return HttpResponseRedirect('user_information')
    pilot_countries = []
    new_user_list = None
    try:
        pilot_countries = PilotCountry.objects.all().order_by('country_name')
        today = date.today()
        seven_day_before = today - timedelta(days=30)
        new_user_list = User.objects.filter(date_joined__gte=seven_day_before)
    except:
        pass
    context = {'pilot_countries': pilot_countries, 'new_user_list': new_user_list}
    if hasattr(request, 'new_users'):
        context['new_users'] = request.new_users
    return render(request, 'scap/index.html', context=context)


def map(request, country=0):
    json_obj = {}
    fc_arr = []
    cs_arr = []
    fc_colls = []
    agb_colls = []
    zoom_level = 3  # global extent center
    lat_long = [44, 10]  # global extent center
    fc_collection = ForestCoverCollection.objects.filter(access_level='Public')
    for fc in fc_collection:
        fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
        fc_years = []
        for fc_yr in fc_files:
            fc_years.append(fc_yr['year'])
        fc_colls.append({'name': str(fc), 'years': fc_years})
    agb_collection = AGBCollection.objects.filter(access_level='Public').values()
    for agb in agb_collection:
        agb_colls.append({'name': agb['name'], 'years': [agb['year']]})
    pc = PilotCountry.objects.filter(id=country).values()
    default_lc = 'JAXA'
    default_agb = 'Saatchi 2000'
    if country > 0:
        pa = PilotCountry.objects.get(id=country)
        if pa.forest_cover_collection is not None:
            default_lc = pa.forest_cover_collection.name
            default_agb = pa.agb_collection.name
    for pilot in pc:
        zoom_level = pilot['zoom_level']
        lat_long = [pilot['latitude'], pilot['longitude']]
        break
    pilot_countries = PilotCountry.objects.all().order_by('country_name')
    iso3 = ''

    try:
        if len(pc) > 0:
            iso3=pc[0]['country_code']
            aois = AOIFeature.objects.filter(iso3=pc[0]['country_code']).exclude(desig_eng='COUNTRY')
            aoi_arr = []
            for aoi in aois:
                aoi_geojson = json.loads(aoi.geom.geojson)
                aoi_geojson['properties'] = {'name': aoi.name, 'ISO3': aoi.iso3, 'desig_eng': aoi.desig_eng}

                aoi_arr.append(aoi_geojson)
            country_shp = AOIFeature.objects.filter(iso3=pc[0]['country_code'], desig_eng='COUNTRY').last()
            country_geojson = json.loads(country_shp.geom.geojson)
            country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                             'desig_eng': country_shp.desig_eng}
            json_obj["data_pa"] = aoi_arr
            country_geojson['coordinates'] = [
                [[[-179, 70],
                  [-179, -70],
                  [179, -70],
                  [179, 70],
                  [-179, 70]]] + country_geojson['coordinates'][0]]
            json_obj["data_country"] = [country_geojson]


        else:
            json_obj["data_pa"] = []
            json_obj["data_country"] = []
        lcs = []
        agbs = []
        if request.user.is_authenticated:
            df_lc_owner = ForestCoverCollection.objects.filter(owner=request.user).values()
            df_lc_public = ForestCoverCollection.objects.filter(access_level='Public').values()
            df_lc = pd.DataFrame((df_lc_owner.union(df_lc_public).values()))

            lcs = df_lc.to_dict('records')
            df_agb_owner = AGBCollection.objects.filter(owner=request.user).values()
            df_agb_public = AGBCollection.objects.filter(access_level='Public').values()
            df_agb = pd.DataFrame(df_agb_owner.union(df_agb_public).values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')
        else:
            df_lc = pd.DataFrame(ForestCoverCollection.objects.filter(access_level='Public').values())
            lcs = df_lc.to_dict('records')
            df_agb = pd.DataFrame(
                AGBCollection.objects.filter(access_level='Public').values())  # Get the AGB dataset data
            agbs = df_agb.to_dict('records')

    except Exception as e:
        print(e)
        json_obj["data_pa"] = []
        json_obj["data_country"] = []
    return render(request, 'scap/map.html',
                  context={'shp_obj': json_obj, 'country_id': country, 'lcs': lcs, 'agbs': agbs,
                           'pilot_countries': pilot_countries,
                           'latitude': lat_long[0], 'longitude': lat_long[1],
                           'zoom_level': zoom_level, 'lat_long': lat_long, 'region': '', 'default_lc': default_lc,
                           'default_agb': default_agb,
                           'fc_colls': fc_colls, 'agb_colls': agb_colls, 'iso3': iso3})


def add_new_collection(request):
    return render(request, 'scap/add_new_collection.html')


def pilot_country(request, country=0):
    json_obj = {}
    fc_colls = []
    try:

        fc_collection = ForestCoverCollection.objects.filter(access_level='Public')

        for fc in fc_collection:
            fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
            fc_years = []
            for fc_yr in fc_files:
                fc_years.append(fc_yr['year'])
            fc_colls.append({'name': str(fc), 'years': fc_years})
        pc = PilotCountry.objects.filter(id=country).values()
        if len(pc) > 0:
            aois = [] # AOIFeature.objects.filter(iso3=pc[0]['country_code']).exclude(desig_eng='COUNTRY')
            aoi_arr = []
            for aoi in aois:
                aoi_geojson = json.loads(aoi.geom.geojson)
                aoi_geojson['properties'] = {'name': aoi.name, 'ISO3': aoi.iso3, 'desig_eng': aoi.desig_eng}
                # aoi_arr.append(aoi_geojson)
            country_shp = AOIFeature.objects.filter(iso3=pc[0]['country_code'], desig_eng='COUNTRY').last()
            country_geojson = json.loads(country_shp.geom.geojson)
            country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                             'desig_eng': country_shp.desig_eng}
            json_obj["data_pa"] = aoi_arr
            # json_obj["data_country"] = [country_geojson]
            country_geojson['coordinates'] = [[[[-179, 70],
                                                [-179, -70],
                                                [179, -70],
                                                [179, 70],
                                                [-179, 70]]] + country_geojson['coordinates'][0]]
            json_obj["data_country"] = [country_geojson]
        else:
            json_obj["data_pa"] = []
            json_obj["data_country"] = []
    except:
        json_obj["data_pa"] = []
        json_obj["data_country"] = []

    pa = PilotCountry.objects.get(id=country)
    iso3 = pa.country_code
    aoi = AOIFeature.objects.get(id=pa.aoi_polygon.id)
    pa_name = aoi.name
    colors = get_available_colors()
    chart, lcs, agbs = fetch_carbon_charts(pa_name, request.user, 'container')
    chart_cs, lcs_cs, agbs_cs = fetch_carbon_stock_charts(pa_name, request.user, 'cs_container')
    chart_fc, lcs_defor = fetch_forest_change_charts(pa_name, request.user, 'container1')
    chart_def, lcs_defor = fetch_deforestation_charts(pa_name, request.user, 'container_deforestation')
    if pa.forest_cover_collection is None:
        default_lc = 'JAXA'
        default_agb = 'Saatchi 2000'
    else:
        default_lc = pa.forest_cover_collection.name
        default_agb = pa.agb_collection.name
    if pa_name == 'Ivory Coast':
        pa_name = "Côte d'Ivoire"
    return render(request, 'scap/pilot_country.html',
                  context={'chart': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fc': chart_fc,
                           'chart_cs': chart_cs, 'chart_def': chart_def,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'lcs_cs': lcs_cs,
                           'agbs_cs': agbs_cs, 'name': pa_name,
                           'desc': pa.country_description, 'tagline': pa.country_tagline, 'image': pa.hero_image.url,
                           'latitude': pa.latitude, 'longitude': pa.longitude, 'zoom_level': pa.zoom_level,
                           'shp_obj': json_obj, 'country': pa.id, 'region': '', 'fc_colls': fc_colls,
                           'default_lc': default_lc, 'default_agb': default_agb, 'iso3': iso3,
                           'global_list': ['CCI', 'ESRI', 'JAXA', 'MODIS', 'WorldCover', 'GFW']})


def protected_aois(request, aoi):
    json_obj = {}
    pa = AOIFeature.objects.get(id=aoi)
    coll = pa.collection.id
    reload = False

    curr_jobs = app.control.inspect().active()
    print(curr_jobs)
    for worker in curr_jobs:
        reload = True
        worker_jobs = curr_jobs[worker]
        for job in worker_jobs:
            if(job['name'] == 'scap.processing.calculate_zonal_statistics' and job['args'][2] == coll):
                reload = True
                break
        if reload:
            break

    pa_name = pa.name
    vall = '{:20,.1f}'.format(pa.rep_area * 100)
    tagline = 'Total area is ' + str(vall) + ' Ha'

    df = gpd.read_file(pa.geom.geojson, driver='GeoJSON')
    df["lon"] = df["geometry"].centroid.x
    df["lat"] = df["geometry"].centroid.y
    fc_colls = []
    fc_collection = ForestCoverCollection.objects.filter(access_level='Public')

    for fc in fc_collection:
        fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
        fc_years = []
        for fc_yr in fc_files:
            fc_years.append(fc_yr['year'])
        fc_colls.append({'name': str(fc), 'years': fc_years})
    try:

        aoi_geojson = json.loads(pa.geom.geojson)
        aoi_geojson['properties'] = {'name': pa_name, 'ISO3': pa.iso3, 'desig_eng': pa.desig_eng}

        json_obj["data_pa"] = [aoi_geojson]
    except:
        json_obj["data_pa"] = []
    colors = get_available_colors()
    pc = PilotCountry.objects.filter(country_code=pa.iso3).first()
    colors = get_available_colors()
    if pc is not None:
        country_shp = AOIFeature.objects.filter(iso3=pc.country_code, desig_eng='COUNTRY').first()
        country_geojson = json.loads(country_shp.geom.geojson)
        country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                         'desig_eng': country_shp.desig_eng}
        json_obj["data_country"] = country_geojson
        pc_name = pc.country_name
        country_id = pc.id
        if pc.forest_cover_collection is None:
            default_lc = 'JAXA'
            default_agb = 'Saatchi 2000'
        else:
            default_lc = pc.forest_cover_collection.name
            default_agb = pc.agb_collection.name
        region_country = pa_name + ', ' + pc_name
        country_description = pc.country_description
        hero_image = pc.hero_image.url
    else:
        json_obj["data_country"] = json_obj["data_pa"]
        default_lc = 'JAXA'
        default_agb = 'Saatchi 2000'
        region_country = 'Custom AOI'
        country_description = ""
        country_id = None
        pc_name = None
        hero_image = '/static/assets/img/pexels-2591408.jpg'

    chart, lcs, agbs = fetch_carbon_charts(pa_name, request.user, 'emissions_chart_pa')
    chart_fc1, lcs_defor = fetch_forest_change_charts_by_aoi(pa_name, request.user, 'container_fcpa')
    chart_cs, lcs_cs, agbs_cs = fetch_carbon_stock_charts(pa_name, request.user, 'cs_container_fcpa')
    chart_def_pa, lcs_defor = fetch_deforestation_charts_by_aoi(pa_name, request.user, 'container_deforestation_pa')
    logger.info(json.dumps(curr_jobs))
    print(json.dumps(curr_jobs))
    return render(request, 'scap/protected_area.html',
                  context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,'chart_cs_pa': chart_cs,'chart_def_pa':chart_def_pa,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor,'lcs_cs':lcs_cs,'agbs_cs':agbs_cs,
                           'region_country': region_country, 'country_desc': country_description,
                           'tagline': tagline, 'image': hero_image, 'country_id': country_id,
                           'latitude': float(df['lat'].iloc[0]), 'longitude': float(df['lon'].iloc[0]),
                           'zoom_level': 10, 'default_lc': default_lc, 'default_agb': default_agb,
                           'country_name': pc_name, 'shp_obj': json_obj, 'fc_colls': fc_colls, 'region': pa_name,
                           'global_list': ['CCI', 'ESRI', 'JAXA', 'MODIS', 'WorldCover', 'GFW'], 'reload': reload, 'curr_jobs': json.dumps(curr_jobs)})


def protected_aois_custom(request, aoi):
    json_obj = {}
    pa = AOIFeature.objects.get(id=aoi)
    pa_name = pa.name
    vall = '{:20,.1f}'.format(pa.rep_area * 100)
    tagline = 'Total area is ' + str(vall) + ' Ha'

    df = gpd.read_file(pa.geom.geojson, driver='GeoJSON')
    df["lon"] = df["geometry"].centroid.x
    df["lat"] = df["geometry"].centroid.y
    fc_colls = []
    fc_collection = ForestCoverCollection.objects.filter(access_level='Public')

    for fc in fc_collection:
        fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
        fc_years = []
        for fc_yr in fc_files:
            fc_years.append(fc_yr['year'])
        fc_colls.append({'name': str(fc), 'years': fc_years})
    try:

        aoi_geojson = json.loads(pa.geom.geojson)
        aoi_geojson['properties'] = {'name': pa_name, 'ISO3': pa.iso3, 'desig_eng': pa.desig_eng}

        json_obj["data_pa"] = [aoi_geojson]
    except:
        json_obj["data_pa"] = []
    colors = get_available_colors()
    pc_name=""
    country_desc=""
    country_id=""
    pc = PilotCountry.objects.filter(country_code=pa.iso3).first()
    if pc is not None:
        country_shp = AOIFeature.objects.filter(iso3=pc.country_code, desig_eng='COUNTRY').first()
        country_geojson = json.loads(country_shp.geom.geojson)
        country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                         'desig_eng': country_shp.desig_eng}
        json_obj["data_country"] = country_geojson
        pc_name = pc.country_name
        country_id = pc.id



    else:
        json_obj["data_country"] = json_obj["data_pa"]

    chart, lcs, agbs = fetch_carbon_charts(pa_name, request.user, 'emissions_chart_pa')
    chart_fc1, lcs_defor = fetch_forest_change_charts_by_aoi(pa_name, request.user, 'container_fcpa')
    chart_cs, lcs_cs, agbs_cs = fetch_carbon_stock_charts(pa_name, request.user, 'cs_container_fcpa')
    chart_def_pa, lcs_defor = fetch_deforestation_charts_by_aoi(pa_name, request.user, 'container_deforestation_pa')
    if len(lcs) == 0:
        default_lc=""
    else:
        default_lc=lcs[0]['name']
    if len(agbs)==0:
        default_agb=""
    else:
        default_agb=agbs[0]['name']

    return render(request, 'scap/protected_area.html',
                  context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                           'chart_cs_pa': chart_cs, 'chart_def_pa': chart_def_pa,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'lcs_cs': lcs_cs,
                           'agbs_cs': agbs_cs,
                           'region_country': 'CUSTOM AOI', 'country_desc':"",
                           'tagline': tagline, 'image':  '/static/assets/img/pexels-2591408.jpg', 'country_id': 0,
                           'latitude': float(df['lat'].iloc[0]), 'longitude': float(df['lon'].iloc[0]),
                           'zoom_level': 10, 'default_lc': default_lc, 'default_agb': default_agb,
                           'country_name': "", 'shp_obj': json_obj, 'fc_colls': fc_colls, 'region': pa_name,
                           'global_list': ['CCI', 'ESRI', 'JAXA', 'MODIS', 'WorldCover', 'GFW']})


def updateColl(request, coll_name):
    coll = ForestCoverCollection.objects.get(username=request.user.username, collection_name=coll_name)
    form = ForestCoverCollection(request.POST, instance=coll)
    if form.is_valid():
        form.save()
    else:
        for field in form:
            print("Field Error:", field.name, field.errors)
    arr = []
    collections = list(
        ForestCoverCollection.objects.filter(username=request.user.username).values('collection_name',
                                                                                    'collection_description').distinct())

    for c in collections:
        arr.append({"name": c['collection_name'], "desc": c['collection_description']})
    return render(request, 'scap/userdata.html', {"coll_list": arr})

def validation(request,type):
    colls=[]
    if type=='fc':
        collections = ForestCoverCollection.objects.filter(approval_status='Submitted')
        ids = []
        names = []
        years = []
        bdata = []
        for c in collections:
            # if c.boundary_file:
            #     sFile = c.boundary_file.path
            #     print(sFile)
            #     gdf = gpd.read_file(sFile)
            #     bdata.append({'id':c.id,'gjson':json.loads(json.dumps(gdf.to_json()))})
            # else:
            #     bdata.append({'id':c.id,'gjson':None})
            ids.append(c.id)
            names.append(c.name)
            tiff_files = ForestCoverFile.objects.filter(collection=c)
            tyears = []
            tfiles=[]
            a_flag=True

            for tfile in tiff_files:
                tyears.append(tfile.year)
                tfiles.append({"year": tfile.year,"cname":c.name,"cid":c.id,"file": Path(tfile.file.name).name, "metadata_link": tfile.metadata_link,"doi_link": tfile.doi_link,"validation_status": tfile.validation_status})
            for tfile in tiff_files:
                if tfile.validation_status!='Approved':
                    a_flag=False
                    break
            colls.append({'coll': c, 'tiff_files': json.dumps(tfiles),'approve_flag':a_flag})
            years.append({'cid':c.id,'years':tyears})

        return render(request, 'scap/validation.html', {'type':type,'colls':colls,'years':json.dumps(years)})
    elif type=='agb':
        collections = AGBCollection.objects.filter(approval_status='Submitted')
        ids = []
        names = []
        years = []
        bdata = []
        for c in collections:
            # if c.boundary_file:
            #     sFile = c.boundary_file.path
            #     print(sFile)
            #     gdf = gpd.read_file(sFile)
            #     bdata.append({'id':c.id,'gjson':json.loads(json.dumps(gdf.to_json()))})
            # else:
            #     bdata.append({'id':c.id,'gjson':None})
            ids.append(c.id)
            names.append(c.name)
            years.append({'cid': c.id, 'years': [c.year]})
        return render(request, 'scap/validation.html', {'type':type,'colls': collections, 'years': json.dumps(years)})
    elif type=='aoi':
        collections= AOICollection.objects.filter(approval_status='Submitted')
        ids = []
        names = []
        for c in collections:
            ids.append(c.id)
            names.append(c.name)
        return render(request, 'scap/validation.html', {'type':type,'colls': collections,'years':json.dumps([])})


def page_not_found_view(request, exception):
    return render(request, 'scap/404.html', status=404)


def logout_view(request):
    """This is for logging out a user"""
    auth.logout(request)
    return redirect("/")


class ManageForestCoverCollections(ListView):
    model = ForestCoverCollection
    template_name = "scap/manage_forest_cover_collections.html"

    def get_queryset(self):
        owner = User.objects.get(username=self.request.user)
        queryset = ForestCoverCollection.objects.filter(owner=owner)
        return queryset


class ManageAGBCollections(ListView):
    model = AGBCollection
    template_name = "scap/manage_agb_collections.html"

    def get_queryset(self):
        owner = User.objects.get(username=self.request.user)

        queryset = AGBCollection.objects.filter(owner=owner)
        return queryset


class ManageAOICollections(ListView):
    model = AOICollection
    template_name = "scap/manage_aoi_collections.html"

    def get_queryset(self):
        owner = User.objects.get(username=self.request.user)
        queryset = AOICollection.objects.filter(owner=owner)
        return queryset


class CreateForestCoverCollection(CreateView):
    model = ForestCoverCollection
    form_class = ForestCoverCollectionForm
    template_name = "scap/create_forest_cover_collection.html"
    success_url = '/forest-cover-collections/'

    def get_context_data(self, **kwargs):
        data = super(CreateForestCoverCollection, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = ForestCoverCollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = ForestCoverCollectionForm()
        data['owner'] = User.objects.get(username=self.request.user).id
        data['operation'] = 'ADD'
        return data

    def get_success_url(self):
        return reverse("edit-forest-cover-collection", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.instance.owner = User.objects.get(username=self.request.user)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        form.instance.owner = User.objects.get(username=self.request.user)
        if not form.is_valid():
            messages.error(self.request,
                           "You already have a forest cover collection with that name, please use a unique name")
        return render(self.request, self.template_name,
                      {'form': form, 'operation': 'ADD', 'owner': User.objects.get(username=self.request.user).id})
        # return HttpResponseRedirect(reverse("create-forest-cover-collection"))


class CreateAGBCollection(CreateView):
    model = AGBCollection
    form_class = AGBCollectionForm
    template_name = "scap/create_agb_collection.html"
    success_url = '/agb-collections/'

    def get_context_data(self, **kwargs):
        data = super(CreateAGBCollection, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = AGBCollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = AGBCollectionForm()

        data['owner'] = User.objects.get(username=self.request.user).id
        data['operation'] = 'ADD'
        data['resolution'] = 100.0
        return data

    def get_success_url(self):
        return reverse("agb-collections")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.instance.owner = User.objects.get(username=self.request.user)
        form.instance.processing_status = 'Staged'
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        collection_type = 'agb'
        collection = AGBCollection.objects.get(name=form.instance.name)
        process_updated_collection.delay(collection.id, collection_type)

        collection.processing_status = "Staged"
        collection.save()
        return HttpResponseRedirect(reverse("agb-collections"))

    def form_invalid(self, form):
        form.instance.owner = User.objects.get(username=self.request.user)
        print(form.errors)
        if not form.is_valid():
            messages.error(self.request,
                           "You already have a AGB collection with that name, please use a unique name")
            return render(self.request, self.template_name,
                          {'form': form, 'operation': 'ADD', 'owner': User.objects.get(username=self.request.user).id})


class CreateAOICollection(CreateView):
    model = AOICollection
    form_class = AOICollectionForm
    template_name = "scap/create_aoi_collection.html"
    success_url = '/aoi-collections/'

    def get_context_data(self, **kwargs):
        data = super(CreateAOICollection, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = AOICollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = AOICollectionForm()

        data['owner'] = User.objects.get(username=self.request.user).id
        data['operation'] = 'ADD'
        return data

    def get_success_url(self):
        return reverse("aoi-collections")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form.instance.owner = User.objects.get(username=self.request.user)
        form.instance.processing_status = 'Staged'

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        collection_type = 'aoi'
        collection = AOICollection.objects.get(name=form.instance.name)
        process_updated_collection.delay(collection.id, collection_type)

        collection.processing_status = "Staged"
        collection.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        form.instance.owner = User.objects.get(username=self.request.user)
        if not form.is_valid():
            messages.error(self.request,
                           "You already have a AOI collection with that name, please use a unique name")
            return render(self.request, self.template_name,
                          {'form': form, 'operation': 'ADD', 'owner': User.objects.get(username=self.request.user).id})


class EditForestCoverCollection(UpdateView):
    model = ForestCoverCollection
    success_url = '/forest-cover-collections/'
    form_class = ForestCoverCollectionForm
    template_name = 'scap/create_forest_cover_collection.html'

    def get_queryset(self):
        qs = super(EditForestCoverCollection, self).get_queryset()
        return qs.filter(owner=User.objects.get(username=self.request.user))

    def get_context_data(self, **kwargs):
        context = super(EditForestCoverCollection, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = ForestCoverCollectionForm(self.request.POST, self.request.FILES, instance=self.object)
            context['owner'] = User.objects.get(username=self.request.user).id

            # filename = self.request.FILES['boundary_file'].name
            # context['boundary_file'] = filename.split('/')[-1]

        else:
            context['form'] = ForestCoverCollectionForm(instance=self.object)
            context['boundary_file'] = self.object.boundary_file.name.split('/')[-1]
            context['owner'] = User.objects.get(username=self.request.user).id

        context['operation'] = 'EDIT'
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ForestCoverCollectionForm(self.request.POST, self.request.FILES, instance=self.object)
        form.instance.owner = User.objects.get(username=self.request.user)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form, operation='EDIT'))


class EditAGBCollection(UpdateView):
    model = AGBCollection
    success_url = '/agb-collections/'
    form_class = AGBCollectionForm
    template_name = 'scap/create_agb_collection.html'

    def get_queryset(self):
        qs = super(EditAGBCollection, self).get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EditAGBCollection, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = AGBCollectionForm(self.request.POST, self.request.FILES, instance=self.object)

            filename = self.request.FILES['boundary_file'].name
            context['boundary_file'] = filename.split('/')[-1]
            source_filename = self.request.FILES['source_file'].name
            context['source_file'] = source_filename.split('/')[-1]
        else:
            context['form'] = AGBCollectionForm(instance=self.object)
            context['boundary_file'] = self.object.boundary_file.name.split('/')[-1]
            context['source_file'] = self.object.source_file.name.split('/')[-1]
        context['operation'] = 'EDIT'
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AGBCollectionForm(self.request.POST, self.request.FILES, instance=self.object)
        if form.is_valid():
            return self.form_valid(form)
        else:

            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form, operation='EDIT'))


class EditAOICollection(UpdateView):
    model = AOICollection
    success_url = '/aoi-collections/'
    form_class = AOICollectionForm
    template_name = 'scap/create_aoi_collection.html'

    def get_queryset(self):
        qs = super(EditAOICollection, self).get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EditAOICollection, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = AOICollectionForm(self.request.POST, self.request.FILES, instance=self.object)

            filename = self.request.FILES['source_file'].name
            context['source_file'] = filename.split('/')[-1]
        else:
            context['form'] = AOICollectionForm(instance=self.object)
            context['source_file'] = self.object.source_file.name.split('/')[-1]
        context['operation'] = 'EDIT'
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AOICollectionForm(self.request.POST, self.request.FILES, instance=self.object)
        if form.is_valid():
            return self.form_valid(form)
        else:

            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form, operation='EDIT'))


class DeleteAOICollection(DeleteView):
    model = AOICollection
    template_name = "scap/delete_aoi_collection.html"
    success_url = reverse_lazy('aoi-collections')


class DeleteAGBCollection(DeleteView):
    model = AGBCollection
    template_name = "scap/delete_agb_collection.html"
    success_url = reverse_lazy('agb-collections')


class DeleteForestCoverCollection(DeleteView):
    model = ForestCoverCollection
    template_name = "scap/delete_forest_cover_collection.html"
    success_url = reverse_lazy('forest-cover-collections')
