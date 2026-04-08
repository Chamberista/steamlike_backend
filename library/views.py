import json 
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from .models import LibraryEntry

def validation_error(details):
    """Devuelve un error de validación en formato estándar"""
    return JsonResponse({
        "error": "validation_error",
        "message": "Datos de entrada inválidos",
        "details": details
    }, status=400)

def duplicate_entry_error(field, value):
    """Devuelve un error de entrada duplicada"""
    return JsonResponse({
        "error": "duplicate_entry",
        "message": f"El campo {field} ya existe",
        "details": {field: f"Ya existe un registro con {field}={value}"}
    }, status=400)

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
            return validation_error({"body": "Body vacío"})
        
        # Validar external_game_id (debe ser número)
        external_game_id = data.get("external_game_id")
        if not external_game_id or not str(external_game_id).isdigit():
            return validation_error({"external_game_id": "Debe ser una cadena de texto"})
        
        # Validar status (debe estar en valores permitidos)
        status = data.get("status", LibraryEntry.STATUS_WISHLIST)
        if status not in LibraryEntry.ALLOWED_STATUSES:
            return validation_error({
                "status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"
            })
        
        # Validar hours_played (debe ser número y >= 0)
        hours_played = data.get("hours_played", 0)
        if not isinstance(hours_played, int) or hours_played < 0:
            return validation_error({"hours_played": "Debe ser un número entero >= 0"})
        
        try:
            entry = LibraryEntry.objects.create(
                external_game_id=external_game_id,
                status=status,
                hours_played=hours_played
            )
        except IntegrityError:
            return duplicate_entry_error("external_game_id", external_game_id)
        
        return JsonResponse({
            "id": entry.id,
            "external_game_id": entry.external_game_id,
            "status": entry.status,
            "hours_played": entry.hours_played
        }, status=201)
    except json.JSONDecodeError:
        return validation_error({"body": "JSON inválido"})
    except Exception as e:
        return validation_error({"server": str(e)})