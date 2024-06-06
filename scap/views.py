import os
import json
import logging
from datetime import datetime,date,timedelta
from pathlib import Path

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
import pandas as pd

from django.contrib.auth.models import User
import shapely
from scap.api import (fetch_forest_change_charts, fetch_forest_change_charts_by_aoi, fetch_carbon_charts,
                      get_available_colors, generate_geodjango_objects_aoi)
from scap.forms import ForestCoverCollectionForm, AOICollectionForm, AGBCollectionForm
from scap.models import (CarbonStatistic, ForestCoverFile, ForestCoverCollection, AOICollection, AGBCollection,
                         PilotCountry, AOIFeature, CurrentTask, ForestCoverStatistic)

from scap.async_tasks import process_updated_collection
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

logger = logging.getLogger("django")


def home(request):
    pilot_countries = []
    new_user_list=None
    try:
        pilot_countries = PilotCountry.objects.all().order_by('country_name')
        today = date.today()
        seven_day_before = today - timedelta(days=30)
        new_user_list = User.objects.filter(date_joined__gte=seven_day_before)
    except:
        pass

    return render(request, 'scap/index.html', context={'pilot_countries': pilot_countries,'new_user_list': new_user_list})


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
                [ [[-179,70],
            [-179,-70],
            [179,-70],
            [179,70],
            [-179,70]]  ] + country_geojson['coordinates'][0]]
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
                           'zoom_level': zoom_level, 'lat_long': lat_long, 'region': '',
                           'fc_colls': fc_colls, 'agb_colls': agb_colls})


def add_new_collection(request):
    return render(request, 'scap/add_new_collection.html')


def pilot_country(request, country=0):
    json_obj = {}
    try:
        fc_colls = []
        fc_collection = ForestCoverCollection.objects.filter(access_level='Public')

        for fc in fc_collection:
            fc_files = ForestCoverFile.objects.filter(collection=fc).values('year')
            fc_years = []
            for fc_yr in fc_files:
                fc_years.append(fc_yr['year'])
            fc_colls.append({'name': str(fc), 'years': fc_years})
        pc = PilotCountry.objects.filter(id=country).values()
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
            # json_obj["data_country"] = [country_geojson]
            country_geojson['coordinates']=[[ [[-179,70],
            [-179,-70],
            [179,-70],
            [179,70],
            [-179,70]]  ]+country_geojson['coordinates'][0]]
            json_obj["data_country"] =  [country_geojson]
        else:
            json_obj["data_pa"] = []
            json_obj["data_country"] = []
    except:
        json_obj["data_pa"] = []
        json_obj["data_country"] = []

    pa = PilotCountry.objects.get(id=country)
    aoi = AOIFeature.objects.get(id=pa.aoi_polygon.id)
    pa_name = aoi.name
    colors = get_available_colors()
    chart, lcs, agbs, chart_cs = fetch_carbon_charts(pa_name, request.user, 'container')
    chart_fc, lcs_defor = fetch_forest_change_charts(pa_name, request.user, 'container1')
    return render(request, 'scap/pilot_country.html',
                  context={'chart': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fc': chart_fc,'chart_cs': chart_cs,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'name': pa_name,
                           'desc': pa.country_description, 'tagline': pa.country_tagline, 'image': pa.hero_image.url,
                           'latitude': pa.latitude, 'longitude': pa.longitude, 'zoom_level': pa.zoom_level,
                           'shp_obj': json_obj, 'country': pa.id, 'region': '', 'fc_colls': fc_colls,
                           'global_list': ['CCI', 'ESRI', 'JAXA', 'MODIS', 'WorldCover', 'GFW']})


def protected_aois(request, aoi):
    json_obj = {}
    pa = AOIFeature.objects.get(id=aoi)
    pa_name = pa.name
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

    pc = PilotCountry.objects.filter(country_code=pa.iso3).first()
    country_shp = AOIFeature.objects.filter(iso3=pc.country_code, desig_eng='COUNTRY').first()
    country_geojson = json.loads(country_shp.geom.geojson)
    country_geojson['properties'] = {'name': country_shp.name, 'ISO3': country_shp.iso3,
                                     'desig_eng': country_shp.desig_eng}
    json_obj["data_country"] = country_geojson
    pc_name = pc.country_name
    country_id = pc.id
    colors = get_available_colors()

    chart, lcs, agbs = fetch_carbon_charts(pa_name, request.user, 'emissions_chart_pa')
    chart_fc1, lcs_defor = fetch_forest_change_charts_by_aoi(pa_name, request.user, 'container_fcpa')
    return render(request, 'scap/protected_area.html',
                  context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor,
                           'region_country': pa_name + ', ' + pc_name, 'country_desc': pc.country_description,
                           'tagline': pc.country_tagline, 'image': pc.hero_image.url, 'country_id': country_id,
                           'latitude': float(df['lat'].iloc[0]), 'longitude': float(df['lon'].iloc[0]),
                           'zoom_level': 10,
                           'country_name': pc_name, 'shp_obj': json_obj, 'fc_colls': fc_colls, 'region': pa_name,
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


def page_not_found_view(request, exception):
    return render(request, 'scap/404.html', status=404)


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
