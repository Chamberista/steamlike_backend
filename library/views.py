import json 
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
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
        "message": "El juego ya existe en la biblioteca",
        "details": {field: "duplicate"}
    }, status=400)

@require_GET
def health(request):
    return JsonResponse({"status": "ok"})

@csrf_exempt
def entries(request):
    """Maneja GET (listar) y POST (crear)"""
    
    if request.method == "GET":
        # Listar todas las entradas
        all_entries = LibraryEntry.objects.all()
        
        data = [
            {
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "status": entry.status,
                "hours_played": entry.hours_played
            }
            for entry in all_entries
        ]
        
        return JsonResponse(data, safe=False)
    
    elif request.method == "POST":
        # Crear una entrada
        try:
            data = json.loads(request.body)
            
            if not data:
                return validation_error({"body": "Body vacío"})
            
            external_game_id = data.get("external_game_id")
            if not external_game_id or not str(external_game_id).isdigit():
                return validation_error({"external_game_id": "Debe ser una cadena de texto"})
            
            status = data.get("status", LibraryEntry.STATUS_WISHLIST)
            if status not in LibraryEntry.ALLOWED_STATUSES:
                return validation_error({
                    "status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"
                })
            
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

@require_GET
def entries_list(request):
    """Devuelve todas las entradas de la biblioteca"""
    entries = LibraryEntry.objects.all()
    
    data = [
        {
            "id": entry.id,
            "external_game_id": entry.external_game_id,
            "status": entry.status,
            "hours_played": entry.hours_played
        }
        for entry in entries
    ]
    
    return JsonResponse(data, safe=False)

@require_http_methods(["GET", "PATCH"])
@csrf_exempt
def entries_detail(request, entry_id):
    """GET: obtiene una entrada. PATCH: actualiza una entrada"""
    
    try:
        # Validar que la entrada existe
        try:
            entry = LibraryEntry.objects.get(id=entry_id)
        except LibraryEntry.DoesNotExist:
            return JsonResponse({
                "error": "not_found",
                "message": "La entrada solicitada no existe"
            }, status=404)
        
        # GET: devolver los datos
        if request.method == "GET":
            return JsonResponse({
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "status": entry.status,
                "hours_played": entry.hours_played
            })
        
        # PATCH: actualizar
        elif request.method == "PATCH":
            data = json.loads(request.body)
            
            if not data:
                return validation_error({"body": "Body vacío"})
            
            allowed_fields = {"status", "hours_played"}
            received_fields = set(data.keys())
            invalid_fields = received_fields - allowed_fields
            
            if invalid_fields:
                return validation_error({
                    "unknown_fields": f"Campos no permitidos: {', '.join(invalid_fields)}"
                })
            
            if "status" in data:
                status = data.get("status")
                if status not in LibraryEntry.ALLOWED_STATUSES:
                    return validation_error({
                        "status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"
                    })
                entry.status = status
            
            if "hours_played" in data:
                hours_played = data.get("hours_played")
                if not isinstance(hours_played, int) or hours_played < 0:
                    return validation_error({
                        "hours_played": "Debe ser un número entero >= 0"
                    })
                entry.hours_played = hours_played
            
            entry.save()
            
            return JsonResponse({
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "status": entry.status,
                "hours_played": entry.hours_played
            }, status=200)
    
    except json.JSONDecodeError:
        return validation_error({"body": "JSON inválido"})
    except Exception as e:
        return validation_error({"server": str(e)})