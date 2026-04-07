from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_GET
def health(request):
    return JsonResponse({"status": "ok"})
@csrf_exempt
@require_POST
def entries(request):
    return JsonResponse({"external_game_id(string)" + "status(whislist)" +"hours_played(0)"})
