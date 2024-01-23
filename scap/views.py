from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from scap.api import generate_fcc_fields, generate_geodjango_objects, generate_from_lambda
# from scap.forms import LoginForm
from scap.generate_files import generate_fc_file, generate_fcc_file
from scap.utils import mask_with_tif

from django.contrib.auth import authenticate, login, logout


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
    # generate_geodjango_objects()
    generate_fc_file(req)


def home(request):
    return render(request, 'scap/index.html')


def peru(request):
    return render(request, 'scap/pilotcountry1.html')

def thailand(request):
    return render(request, 'scap/pilotcountry2.html')


def aoi(request):
    return render(request, 'scap/aoi.html')


def addData(request):
    return render(request, 'scap/addData.html')
