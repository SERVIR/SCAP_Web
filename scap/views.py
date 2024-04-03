import os
import json
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from django.contrib.auth.models import User

from scap.api import (fetch_forest_change_charts, fetch_forest_change_charts_by_aoi, fetch_carbon_charts,
                      get_available_colors, generate_geodjango_objects_aoi)
from scap.forms import ForestCoverCollectionForm, AOICollectionForm, AGBCollectionForm
from scap.models import CarbonStatistic, ForestCoverFile, ForestCoverCollection, AOICollection, AGBCollection, \
    PilotCountry, AOIFeature

from scap.async_tasks import process_agb_collection, process_aoi_collection

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
config = json.load(f)

def home(request):
    pilot_countries=[]
    try:
        pilot_countries=PilotCountry.objects.all().order_by('country_name')
    except:
        pass

    return render(request, 'scap/index.html',context={'pilot_countries':pilot_countries})

def map(request):
    return render(request, 'scap/map.html')


def add_new_collection(request):
    return render(request, 'scap/add_new_collection.html')


def pilot_country(request, country=1):
    pa = PilotCountry.objects.get(id=country)

    try:
        pa_name=pa.country_name
    except:
        pa_name = "Peru"
    colors = get_available_colors()
    chart, lcs, agbs = fetch_carbon_charts(pa_name, 'container')
    chart_fc, lcs_defor = fetch_forest_change_charts(pa_name, 'container1')
    return render(request, 'scap/pilot_country.html',
                  context={'chart': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fc': chart_fc,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor,'name':pa_name,'desc':pa.country_description,'image':pa.hero_image.url    })


def protected_aois(request, aoi):
    try:
        pa = AOIFeature.objects.get(id=aoi)
        try:
            pa_name = pa.name
            pc=PilotCountry.objects.get(country_code=pa.iso3)
            pc_name=pc.country_name
        except:
            pa_name = "Mantanay"
            pc_name = "Peru"
        colors = get_available_colors()
        chart, lcs, agbs = fetch_carbon_charts(pa_name, 'emissions_chart_pa')
        chart_fc1, lcs_defor = fetch_forest_change_charts_by_aoi(aoi, 'container_fcpa')
        return render(request, 'scap/protected_area.html',
                      context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                               'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'region_country': pa_name+', '+pc_name,'country_desc':pc.country_description,'image':pc.hero_image.url})
    except Exception as e:
        return render(request, 'scap/protected_area.html')



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
        data['resolution'] = 100.0
        return data

    def get_success_url(self):
        return reverse("edit-forest-cover-collection", kwargs={"pk": self.object.pk})

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if not form.is_valid():
            messages.add_message(self.request, messages.WARNING, form.errors)

        return HttpResponseRedirect(reverse("create-forest-cover-collection"))


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
        form.instance.processing_status='Staged'
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        process_agb_collection.delay(form.instance.name)
        return HttpResponseRedirect(reverse("agb-collections"))

    def form_invalid(self, form):
        if not form.is_valid():
            messages.add_message(self.request, messages.WARNING, form.errors)
            print(form)
            print(form.errors)

        return HttpResponseRedirect(reverse("create-agb-collection"))


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
        form.instance.processing_status='Staged'

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        process_aoi_collection.delay(form.instance.name)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        if not form.is_valid():
            messages.add_message(self.request, messages.WARNING, form.errors)
            print(form)
            print(form.errors)

        return HttpResponseRedirect(reverse("add-aoi-collection"))


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
            context['form'] = ForestCoverCollectionForm(self.request.POST, instance=self.object)
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
        form = ForestCoverCollectionForm(self.request.POST, instance=self.object)
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
        return qs.filter(username=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EditAGBCollection, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = AGBCollectionForm(self.request.POST, self.request.FILES, instance=self.object)

            filename = self.request.FILES['boundary_file'].name
            context['agb_boundary_file'] = filename.split('/')[-1]
        else:
            context['form'] = AGBCollectionForm(instance=self.object)
            context['agb_boundary_file'] = self.object.agb_boundary_file.name.split('/')[-1]
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
        return qs.filter(username=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(EditAOICollection, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = AOICollectionForm(self.request.POST, self.request.FILES, instance=self.object)

            filename = self.request.FILES['aoi_shape_file'].name
            context['aoi_shape_file'] = filename.split('/')[-1]
        else:
            context['form'] = AOICollectionForm(instance=self.object)
            context['aoi_shape_file'] = self.object.aoi_shape_file.name.split('/')[-1]
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
