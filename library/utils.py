import json
from django.http import JsonResponse


def validation_error(details):
    return JsonResponse({
        "error": "validation_error",
        "message": "Datos de entrada inválidos",
        "details": details
    }, status=400)


def unauthorized_error():
    return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)


def not_found_error():
    return JsonResponse({"error": "not_found", "message": "La entrada solicitada no existe"}, status=404)


def duplicate_entry_error(field, value):
    return JsonResponse({
        "error": "duplicate_entry",
        "message": "El juego ya existe en la biblioteca",
        "details": {field: "duplicate"}
    }, status=400)


def parse_json_body(request):
    """
    Parsea el body JSON del request.
    Devuelve (data, None) si tiene éxito o (None, JsonResponse) si falla.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return None, validation_error({"body": "JSON inválido"})
    if not data:
        return None, validation_error({"body": "Body vacío"})
    return data, None


def serialize_entry(entry):
    return {
        "id": entry.id,
        "external_game_id": entry.external_game_id,
        "status": entry.status,
        "hours_played": entry.hours_played,
    }
