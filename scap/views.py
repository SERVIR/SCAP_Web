import numpy as np
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
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
from scap.forms import NewCollectionForm, TiffFileFormSet
from scap.generate_files import generate_fc_file, generate_fcc_file
from scap.utils import mask_with_tif
import pandas as pd
from django.contrib.auth import authenticate, login, logout
from scap.models import ForestCoverSource, AGBSource, Emissions, ForestCoverChange, BoundaryFiles, NewCollection, \
    TiffFile
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
        # generate_fcc_fields("CCI", 2007)
        # generate_geodjango_objects_aoi()
        generate_geodjango_objects_boundary()
        # generate_fc_file(req)
        return HttpResponse("The script ran successfully")
    except Exception as e:
        return HttpResponse(str(e))


def home(request):
    return render(request, 'scap/index.html')


def map(request):
    return render(request, 'scap/map.html')


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
    coll = NewCollection.objects.get(username=request.user.username, collection_name=coll_name)
    return render(request, 'scap/editData.html', {'coll': coll})


def deleteColl(request, coll_name):
    coll = NewCollection.objects.filter(username=request.user.username, collection_name=coll_name)
    coll.delete()
    return redirect('/user-data/')


def updateColl(request, coll_name):
    coll = NewCollection.objects.get(username=request.user.username, collection_name=coll_name)
    form = NewCollectionForm(request.POST, instance=coll)
    # print(form)

    if form.is_valid():
        form.save()
    else:
        for field in form:
            print("Field Error:", field.name, field.errors)
    arr = []
    collections = list(
        NewCollection.objects.filter(username=request.user.username).values('collection_name',
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


class TiffFileCreate(CreateView):
    model = NewCollection
    fields = ['collection_name', 'collection_description', 'boundary_file', 'access_level',
              'projection']
    success_url = reverse_lazy('userData')

    def get_context_data(self, **kwargs):
        data = super(TiffFileCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['tifffiles'] = TiffFileFormSet(self.request.POST, self.request.FILES)
        else:
            data['tifffiles'] = TiffFileFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        tifffiles = context['tifffiles']
        with transaction.atomic():
            self.object = form.save()

            if tifffiles.is_valid():
                tifffiles.instance = self.object
                tifffiles.save()
        return super(TiffFileCreate, self).form_valid(form)


# def TiffFileUpdateView(request, id):
#     coll = NewCollection.objects.get(id=id)
#     tiff = TiffFile.objects.get(collection_id=id)
#     dato = NewCollection.objects.filter(tifffile=tiff)
#     if request.method == 'POST':
#         dati_formset = TiffFileFormSet(request.POST, request.FILES, queryset=dato)
#
#         if dati_formset.is_valid():
#             for dato in dati_formset:
#                 dato.save()
#
#             return redirect('/')
#     else:
#         dati_formset = TiffFileFormSet(queryset=dato)
#
#     context = {'form': coll, 'tifffiles_obj': tiff, 'tifffiles': dati_formset}
#     return render(request, 'scap/newcollection_form.html', context)


class NewCollectionList(ListView):
    model = NewCollection
    def get_queryset(self):
        queryset = NewCollection.objects.filter(username=self.request.user)
        print(queryset)
        return queryset
class NewCollectionCreate(CreateView):
    model = NewCollection
    form_class = NewCollectionForm
    template_name = "scap/newcollection_form.html"
    success_url = reverse_lazy('userData')

    def get_context_data(self, **kwargs):
        data = super(NewCollectionCreate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['tifffiles'] = TiffFileFormSet(self.request.POST, self.request.FILES)
            data['form'] = NewCollectionForm(self.request.POST, self.request.FILES)
        else:
            data['tifffiles'] = TiffFileFormSet()
            data['form'] = NewCollectionForm()
        data['operation']='ADD'
        # print('This is context data {}'.format(data['form']))
        return data

    def get_success_url(self):
        return reverse("userData")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        education_formset = TiffFileFormSet(request.POST,request.FILES)

        if form.is_valid() and education_formset.is_valid():
            return self.form_valid(form, education_formset)
        else:
            return self.form_invalid(form,education_formset)

    def form_valid(self, form, expense_line_item_form):
        self.object = form.save()
        expense_line_item_form.instance = self.object
        expense_line_item_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, expense_line_item_form):
        return self.render_to_response(
            self.get_context_data(form=form, tifffiles=expense_line_item_form, operation='ADD'))

class NewCollectionUpdate(UpdateView):
    model = NewCollection
    success_url = '/user-data/'
    form_class = NewCollectionForm
    template_name = 'scap/newcollection_form.html'

    def get_context_data(self, **kwargs):
        print('from get')
        context = super(NewCollectionUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            context['form'] = NewCollectionForm(self.request.POST,self.request.FILES, instance=self.object)
            context['tifffiles'] = TiffFileFormSet(self.request.POST,self.request.FILES,
                                                        instance=self.object)
            filename = self.request.FILES['boundary_file'].name
            context['boundary_file'] =filename
        else:
            context['form'] = NewCollectionForm(instance=self.object)
            context['tifffiles'] = TiffFileFormSet(instance=self.object)
            context['boundary_file'] = self.object.boundary_file.name
        context['operation'] = 'EDIT'
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = NewCollectionForm(self.request.POST,self.request.FILES,instance=self.object)
        expense_line_item_form = TiffFileFormSet(self.request.POST,self.request.FILES,instance=self.object)
        print('in post')
        print(form.is_valid())
        print(expense_line_item_form.is_valid())
        if (form.is_valid() and expense_line_item_form.is_valid()):
            print('form is valid')
            return self.form_valid(form, expense_line_item_form)
        else:
            print(expense_line_item_form.errors)

            return self.form_invalid(form, expense_line_item_form)

    def form_valid(self, form, expense_line_item_form):
        self.object = form.save()
        expense_line_item_form.instance = self.object
        expense_line_item_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, expense_line_item_form):
        return self.render_to_response(
            self.get_context_data(form=form, tifffiles=expense_line_item_form, operation='EDIT'))



class NewCollectionDelete(DeleteView):
    model = NewCollection
    success_url = reverse_lazy('userData')
