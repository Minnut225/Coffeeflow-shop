from django.urls import path, include, re_path
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

def root_view(request):
    return JsonResponse({"message": "Welcome to CoffeeFlow Django API"})

urlpatterns = [
    path('health', health_check),
    path('health/', health_check),
    path('', root_view),
    path('api/v1/', include('api.urls')),
]
