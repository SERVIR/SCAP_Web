from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from scap.api import generate_fcc_fields, generate_geodjango_objects
from scap.generate_files import generate_fc_file


# A test URL to test the methods@csrf_exempt
def test(req):
    generate_fcc_fields("Mapbiomas", 2001)
    return HttpResponse("The fields were generated. Please check http://127.0.0.1:8000/admin/scap/forestcoverchange/")
    # generate_geodjango_objects()
    # generate_fc_file(req)

def home(request):
    return render(request, 'home.html')