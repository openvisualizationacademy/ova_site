from django.http import JsonResponse


def chrome_devtools_dummy(request):
    return JsonResponse({
        "status": "ok",
        "message": "Dummy response for Chrome DevTools"
    })
