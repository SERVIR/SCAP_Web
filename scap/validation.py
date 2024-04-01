import doi

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def doi_valid(request,pk):
    if request.POST.get('doi')=='':
        return JsonResponse({"url": ""})
    try:
        url = doi.validate_doi(request.POST.get('doi'))
        return JsonResponse({"url": url})
    except Exception as e:
        return JsonResponse({"error": "error"})