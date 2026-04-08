import json 
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import LibraryEntry

@require_GET
def health(request):
    return JsonResponse({"status": "ok"})

@csrf_exempt
@require_POST
def entries(request):
    try:
        data = json.loads(request.body)
        
        # Validar que body no esté vacío
        if not data:
            return JsonResponse({"error": "Body vacío"}, status=400)
        
        # Validar external_game_id (debe ser número)
        external_game_id = data.get("external_game_id")
        if not external_game_id or not str(external_game_id).isdigit():
            return JsonResponse({"error": "external_game_id debe ser un número"}, status=400)
        
        # Validar status (debe estar en valores permitidos)
        status = data.get("status", LibraryEntry.STATUS_WISHLIST)
        if status not in LibraryEntry.ALLOWED_STATUSES:
            return JsonResponse({"error": f"status debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"}, status=400)
        
        # Validar hours_played (debe ser número y >= 0)
        hours_played = data.get("hours_played", 0)
        if not isinstance(hours_played, int) or hours_played < 0:
            return JsonResponse({"error": "hours_played debe ser un número entero >= 0"}, status=400)
        
        entry = LibraryEntry.objects.create(
            external_game_id=external_game_id,
            status=status,
            hours_played=hours_played
        )
        
        return JsonResponse({
            "id": entry.id,
            "external_game_id": entry.external_game_id,
            "status": entry.status,
            "hours_played": entry.hours_played
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)