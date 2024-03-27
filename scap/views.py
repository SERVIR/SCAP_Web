import os
from datetime import datetime
from pathlib import Path

import numpy as np
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import redirect_to_login
from django.core.files.storage import FileSystemStorage
from django.db import transaction, IntegrityError
from django.forms import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template.context import RequestContext
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DeleteView
from pandas_highcharts.core import serialize
from scap.api import generate_fcc_fields, generate_geodjango_objects_aoi, generate_from_lambda, \
    generate_geodjango_objects_boundary
from scap.forms import ForestCoverCollectionForm, AOICollectionForm, AGBCollectionForm
from scap.generate_files import generate_fc_file, generate_fcc_file
from scap.utils import mask_with_tif
import pandas as pd
from django.contrib.auth import authenticate, login, logout
from scap.models import ForestCoverSource, AGBSource, Emissions, ForestCoverChange, BoundaryFiles, \
    TiffFile, ForestCoverCollection, AOICollection, AGBCollection
from ScapTestProject import settings
import json

from django.shortcuts import render, get_object_or_404

BASE_DIR = Path(__file__).resolve().parent.parent
f = open(str(BASE_DIR) + '/data.json', )
params = json.load(f)


# A test URL to test the methods
@csrf_exempt
def test(req):
    try:
        # test_method()
        # generate_from_lambda()
        # mask_with_tif()
        # generate_fcc_file(req)
        # generate_fcc_fields("CCI", 2007)
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

def add_user_data(request):
    return render(request, 'scap/add_user_data.html')
def generate_colors():
    colors = []
    try:
        # generating list of colors from  the text file
        with open(settings.STATIC_ROOT + '/data/palette.txt') as f:
            for line in f:
                row = line.strip()
                temp = {}
                temp['LC'] = int(row.split(',')[0][2:])
                temp['AGB'] = int(row.split(',')[1][3:])
                temp['color'] = row.split(',')[2]
                colors.append(temp)
    except Exception as e:
        print(str(e))
    return colors


def generate_emissions(pa_name, container):
    try:
        print("from emis")
        # generating highcharts chart object from python using pandas(emissions chart)
        df_lc = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es', 'pais').order_by(
            'id')))
        lcs = df_lc.to_dict('records')
        df_agb = pd.DataFrame(list(AGBSource.objects.all().values('agb_id', 'agb_name')))  # Get the AGB dataset data
        agbs = df_agb.to_dict('records')
        df = pd.DataFrame(list(Emissions.objects.filter(aoi_id__name=pa_name).values()))
        df["lc_id_id"] = "LC" + df["lc_id_id"].apply(str)
        df["agb_id_id"] = "AGB" + df["agb_id_id"]  # Add the prefix AGB to the AGB id column
        grouped_data = df.groupby(['year', 'lc_id_id', 'agb_id_id'])['lc_agb_value'].sum().reset_index()
        pivot_table = pd.pivot_table(grouped_data, values='lc_agb_value', columns=['lc_id_id', 'agb_id_id'],
                                     index='year',
                                     fill_value=None)
        chart = serialize(pivot_table, render_to=container, output_type='json', type='spline',
                          title='Emissions: ' + pa_name)
    except Exception as e:
        error_msg = "cannot generate chart data for emissions"
        print(str(e))
    return chart, lcs, agbs


def generate_fc(pa_name, container):
    # generating highcharts chart object from python using pandas(forest cover change chart)
    df_defor = pd.DataFrame(
        list(ForestCoverChange.objects.filter(aoi__name=pa_name).values()))  # Get the ForestCoverChange dataset data
    df_lc_defor = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es').order_by(
        'id')))
    lcs_defor = df_lc_defor.to_dict('records')
    df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
    df_defor["nfc"] = df_defor['forest_gain'] - df_defor['forest_loss']
    years_defor = list(df_defor['year'].unique())
    pivot_table_defor = pd.pivot_table(df_defor, values='nfc', columns=['fc_source_id'],
                                       index='year', fill_value=None)
    chart_fc = serialize(pivot_table_defor, render_to=container, output_type='json', type='spline',
                         xticks=years_defor,
                         title='Change in Forest Cover: ' + pa_name, )
    return chart_fc, lcs_defor


def generate_fc_with_area(pa_name, container):
    # generating highcharts chart object from python using pandas(forest cover change chart)
    df_defor = pd.DataFrame(list(ForestCoverChange.objects.filter(aoi__name=pa_name).values()))
    df_lc_defor = pd.DataFrame(list(BoundaryFiles.objects.all().values('id', 'name_es').order_by(
        'id')))
    lcs_defor = df_lc_defor.to_dict('records')
    df_defor["NFC"] = df_defor['forest_gain'] - df_defor['forest_loss']
    df_defor["TotalArea"] = df_defor["initial_forest_area"] + df_defor["NFC"]
    df_defor['fc_source_id'] = 'LC' + df_defor['fc_source_id'].apply(str)
    years_defor = list(df_defor['year'].unique())

    pivot_table_defor1 = pd.pivot_table(df_defor, values='NFC', columns=['fc_source_id'],
                                        index='year', fill_value=None)
    # chart_fc1 = serialize(pivot_table_defor1, render_to='container_fcpa', output_type='json', type='spline',
    #                      xticks=years_defor,
    #                      title="Protected Area: " + pa_name,secondary_y=['TotalArea'])
    chart_fc1 = serialize(pivot_table_defor1, render_to=container, output_type='json', type='spline',
                          xticks=years_defor,
                          title="Change in Forest Cover: " + pa_name)
    return chart_fc1, lcs_defor


# This page shows when someone clicks on 'Peru' tile in home page
def pilot_country(request, country):
    print(country)
    pa_name = country

    if country == 'None':
        pa_name = "Peru"
    colors = generate_colors()
    chart, lcs, agbs = generate_emissions(pa_name, 'container')
    chart_fc, lcs_defor = generate_fc(pa_name, 'container1')
    return render(request, 'scap/pilotcountry.html',
                  context={'chart': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fc': chart_fc,
                           'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor})


# This page shows when someone clicks on any protected area in protected areas page
def protected_aois(request, aoi):
    try:
        pa_name = aoi
        if pa_name is None:
            pa_name = 'Mantanay'
        colors = generate_colors()
        chart, lcs, agbs = generate_emissions(pa_name, 'emissions_chart_pa')
        chart_fc1, lcs_defor = generate_fc_with_area(pa_name, 'container_fcpa')
        return render(request, 'scap/protected_areas.html',
                      context={'chart_epa': chart, 'lcs': lcs, 'agbs': agbs, 'colors': colors, 'chart_fcpa': chart_fc1,
                               'lcs_defor': json.dumps(lcs_defor), 'lc_data': lcs_defor, 'region_country': pa_name})
    except Exception as e:
        return render(request, 'scap/protected_areas.html')


def userData(request):
    arr = []
    collections = list(
        NewCollection.objects.filter(username=request.user.username).values('collection_name',
                                                                            'collection_description').distinct())
    # print(collections)
    for c in collections:
        arr.append({"name": c['collection_name'], "desc": c['collection_description']})

    return render(request, 'scap/userdata.html', {"coll_list": arr})


# def addColl(request):
#     # if request.method == 'POST':
#     #     form = NewCollectionForm(request.POST, request.FILES)
#     #
#     #     if form.is_valid():
#     #         try:
#     #             print("from try")
#     #             form.save()
#     #             # return redirect('/')
#     #         except Exception as e:
#     #             print(str(e))
#     #     else:
#     #         for field in form:
#     #             print("Field Error:", field.name, field.errors)
#     #
#     # else:
#     #     form=NewCollectionForm()
#     # return render(request, 'scap/addData.html', {'form': form})
#     if request.method == 'POST':
#         new_coll_form = NewCollectionForm(request.POST, prefix='new_coll')
#         tifffile_formset = TiffFileFormset(request.POST, request.FILES, prefix='tiff')
#         if new_coll_form.is_valid() and tifffile_formset.is_valid():
#             invoice = new_coll_form.save()
#             # I recreate my lineitem_formset bound to the new invoice instance
#             for form in tifffile_formset:
#                 # extract name from each form and save
#                 file = form.cleaned_data.get('file')
#                 # save book instance
#                 if file:
#                     TiffFile(file=file).save()
#             # if 'submit_more' in request.POST:
#             #     return HttpResponseRedirect(reverse('invoices:add_invoice'))
#             # else:
#             #     return HttpResponseRedirect(reverse('invoices:get_invoices'))
#             return render(request, 'scap/addData.html', {
#                 'message': "Check your form",
#                 'invoice_form': new_coll_form,
#                 'lineitem_formset': tifffile_formset,
#             })
#         else:
#             for field in tifffile_formset:
#                 print("Field Error:", field.name, field.errors)
#             return render(request, 'scap/addData.html', {
#                 'message': "Check your form",
#                 'invoice_form': new_coll_form,
#                 'lineitem_formset': tifffile_formset,
#             })

def editColl(request, coll_name):
    coll = ForestCoverCollection.objects.get(username=request.user.username, collection_name=coll_name)
    return render(request, 'scap/editData.html', {'coll': coll})


def deleteColl(request, coll_name):
    coll = ForestCoverCollection.objects.filter(username=request.user.username, collection_name=coll_name)
    coll.delete()
    return redirect('/user-data/')


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
    # print(collections)
    for c in collections:
        arr.append({"name": c['collection_name'], "desc": c['collection_description']})
    return render(request, 'scap/userdata.html', {"coll_list": arr})


def signup_redirect(request):
    messages.error(request, "Something wrong here, it may be that you already have account!")
    return redirect("homepage")


def thailand(request):
    return render(request, 'scap/pilotcountry2.html')


def aoi(request):
    return render(request, 'scap/aoi.html')


class ForestCoverCollectionList(ListView):
    model = ForestCoverCollection

    def get_queryset(self):
        queryset = ForestCoverCollection.objects.filter(username=self.request.user)
        return queryset


class AGBCollectionList(ListView):
    model = AGBCollection

    def get_queryset(self):
        queryset = AGBCollection.objects.filter(username=self.request.user)
        return queryset


class AOICollectionList(ListView):
    model = AOICollection

    def get_queryset(self):
        queryset = AOICollection.objects.filter(username=self.request.user)
        return queryset


class ForestCoverCollectionCreate(CreateView):
    model = ForestCoverCollection
    form_class = ForestCoverCollectionForm
    template_name = "scap/forestcovercollection_form.html"
    success_url = '/user-data/'

    def get_context_data(self, **kwargs):
        data = super(ForestCoverCollectionCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = ForestCoverCollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = ForestCoverCollectionForm()

        data['operation'] = 'ADD'
        data['resolution'] = 100.0
        return data

    def get_success_url(self):
        return reverse("userData")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        print(self.request.FILES)
        dirname = datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
        username = self.request.user
        file_path = params['PATH_TO_NEW_TIFFS'] + str(username) + '\\Public'
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        folder = file_path + '/'.format(dirname)
        uploaded_file = request.FILES['boundary_file']
        fs = FileSystemStorage(location=folder)
        name = fs.save(uploaded_file.name, uploaded_file)
        form.instance.username = self.request.user
        form.instance.resolution = 100.0
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

        return HttpResponseRedirect(reverse("add-coll"))


def page_not_found_view(request, exception):
    return render(request, 'scap/404.html', status=404)


class AGBCollectionCreate(CreateView):
    model = AGBCollection
    form_class = AGBCollectionForm
    template_name = "scap/agbcollection_form.html"
    success_url = '/agb-data/'

    def get_context_data(self, **kwargs):
        data = super(AGBCollectionCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = AGBCollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = AGBCollectionForm()

        data['operation'] = 'ADD'
        data['resolution'] = 100.0
        return data

    def get_success_url(self):
        return reverse("agbData")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        print(self.request.FILES)
        dirname = datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
        username = self.request.user
        file_path = params['PATH_TO_NEW_TIFFS'] + str(username) + '\\Public'
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        folder = file_path + '/'.format(dirname)
        uploaded_file = request.FILES['agb_boundary_file']
        fs = FileSystemStorage(location=folder)
        name = fs.save(uploaded_file.name, uploaded_file)
        form.instance.username = self.request.user
        form.instance.resolution = 100.0
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

        return HttpResponseRedirect(reverse("add-agb"))


class ForestCoverCollectionUpdate(UpdateView):
    model = ForestCoverCollection
    success_url = '/user-data/'
    form_class = ForestCoverCollectionForm
    template_name = 'scap/forestcovercollection_form.html'

    def get_queryset(self):
        qs = super(ForestCoverCollectionUpdate, self).get_queryset()
        return qs.filter(username=self.request.user)

    def get_context_data(self, **kwargs):
        print('get con')
        context = super(ForestCoverCollectionUpdate, self).get_context_data(**kwargs)

        if self.request.POST:
            context['form'] = ForestCoverCollectionForm(self.request.POST, self.request.FILES, instance=self.object)

            filename = self.request.FILES['boundary_file'].name
            context['boundary_file'] = filename
        else:
            context['form'] = ForestCoverCollectionForm(instance=self.object)
            context['boundary_file'] = self.object.boundary_file.name
        context['operation'] = 'EDIT'
        return context

    def post(self, request, *args, **kwargs):
        print('get post`')
        self.object = self.get_object()
        form = ForestCoverCollectionForm(self.request.POST, self.request.FILES, instance=self.object)
        print('in post')
        print(form.is_valid())
        if (form.is_valid()):
            print('form is valid')
            return self.form_valid(form)
        else:

            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print("invalid")
        return self.render_to_response(
            self.get_context_data(form=form, operation='EDIT'))


class ForestCoverCollectionDelete(DeleteView):
    model = ForestCoverCollection
    success_url = reverse_lazy('userData')


class AOICollectionCreate(CreateView):
    model = AOICollection
    form_class = AOICollectionForm
    template_name = "scap/aoicollection_form.html"
    success_url = '/aoi-data/'

    def get_context_data(self, **kwargs):
        data = super(AOICollectionCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['form'] = AOICollectionForm(self.request.POST, self.request.FILES)

        else:
            data['form'] = AOICollectionForm()

        data['operation'] = 'ADD'
        return data

    def get_success_url(self):
        return reverse("aoiData")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        print(self.request.FILES)
        dirname = datetime.now().strftime('%Y.%m.%d.%H.%M.%S')
        username = self.request.user
        file_path = params['PATH_TO_NEW_AOIS'] + str(username) + '\\Public'
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        folder = file_path + '/'.format(dirname)
        uploaded_file = request.FILES['aoi_shape_file']
        fs = FileSystemStorage(location=folder)
        name = fs.save(uploaded_file.name, uploaded_file)
        form.instance.username = self.request.user
        form.instance.resolution = 100.0
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

        return HttpResponseRedirect(reverse("add-aoi"))


class AOICollectionDelete(DeleteView):
    model = AOICollection
    success_url = reverse_lazy('agbData')


class AGBCollectionDelete(DeleteView):
    model = AGBCollection
    success_url = reverse_lazy('agbData')
