import requests
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.conf import settings
from .models import LibraryEntry
from .utils import (
    validation_error, unauthorized_error, not_found_error,
    duplicate_entry_error, parse_json_body, serialize_entry,
)
from .email_service import EmailService, ExternalServiceUnavailable, ExternalServiceError

_CHEAPSHARK_BASE = "https://www.cheapshark.com/api/1.0/games"
_CHEAPSHARK_TIMEOUT = 8


def _fetch_cheapshark(params: dict):
    try:
        response = requests.get(_CHEAPSHARK_BASE, params=params, timeout=_CHEAPSHARK_TIMEOUT)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return None, JsonResponse(
            {"error": "external_service_unavailable", "message": "El catálogo externo no está disponible. Inténtalo más tarde."},
            status=503,
        )
    if not response.ok:
        return None, JsonResponse(
            {"error": "external_service_error", "message": "Error al consultar el catálogo externo."},
            status=502,
        )
    try:
        return response.json(), None
    except ValueError:
        return None, JsonResponse(
            {"error": "external_service_error", "message": "Error al consultar el catálogo externo."},
            status=502,
        )

User = get_user_model()


# ===== AUTH ENDPOINTS =====

@require_http_methods(["POST"])
@csrf_exempt
def register(request):
    """POST /api/auth/register/"""
    data, err = parse_json_body(request)
    if err:
        return err

    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if username is None:
        return validation_error({"username": "Campo requerido"})
    if password is None:
        return validation_error({"password": "Campo requerido"})
    if email is None:
        return validation_error({"email": "Campo requerido"})
    if not isinstance(username, str):
        return validation_error({"username": "Debe ser texto"})
    if not isinstance(password, str):
        return validation_error({"password": "Debe ser texto"})
    if not isinstance(email, str):
        return validation_error({"email": "Debe ser texto"})
    if not username.strip():
        return validation_error({"username": "No puede estar vacío"})
    if len(password) < 8:
        return validation_error({"password": "Mínimo 8 caracteres"})
    if "@" not in email or not email.strip():
        return validation_error({"email": "Formato de email inválido"})
    if User.objects.filter(username=username).exists():
        return validation_error({"username": "Ya existe"})

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        return JsonResponse({"id": user.id, "username": user.username, "email": user.email}, status=201)
    except Exception as e:
        return validation_error({"server": str(e)})


@require_http_methods(["POST"])
@csrf_exempt
def logout_view(request):
    """POST /api/auth/logout/"""
    logout(request)
    return HttpResponse(status=204)


@require_http_methods(["POST"])
@csrf_exempt
def login_view(request):
    """POST /api/auth/login/"""
    data, err = parse_json_body(request)
    if err:
        return err

    username = data.get("username")
    password = data.get("password")

    if username is None or password is None:
        return validation_error({"fields": "username y password son requeridos"})
    if not isinstance(username, str) or not isinstance(password, str):
        return validation_error({"fields": "username y password deben ser texto"})

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"error": "unauthorized", "message": "Credenciales incorrectas"}, status=401)

    login(request, user)
    return JsonResponse({"id": user.id, "username": user.username}, status=200)


@require_GET
def me(request):
    """GET /api/users/me/"""
    if not request.user.is_authenticated:
        return unauthorized_error()
    return JsonResponse({"id": request.user.id, "username": request.user.username}, status=200)


@require_http_methods(["POST"])
@csrf_exempt
def change_password(request):
    """POST /api/users/me/password/"""
    if not request.user.is_authenticated:
        return unauthorized_error()

    data, err = parse_json_body(request)
    if err:
        return err

    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if current_password is None:
        return validation_error({"current_password": "Campo requerido"})
    if new_password is None:
        return validation_error({"new_password": "Campo requerido"})
    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return validation_error({"fields": "Deben ser texto"})
    if not request.user.check_password(current_password):
        return validation_error({"current_password": "Contraseña actual incorrecta"})
    if len(new_password) < 8:
        return validation_error({"new_password": "Mínimo 8 caracteres"})

    request.user.set_password(new_password)
    request.user.save()
    return JsonResponse({"ok": True}, status=200)


# ===== LIBRARY ENDPOINTS =====

@require_GET
def health(request):
    """GET /api/health/"""
    return JsonResponse({"status": "ok"})


@csrf_exempt
def entries(request):
    """GET /api/library/entries/ — listar. POST — crear."""
    if not request.user.is_authenticated:
        return unauthorized_error()

    if request.method == "GET":
        data = [serialize_entry(e) for e in LibraryEntry.objects.filter(user=request.user)]
        return JsonResponse(data, safe=False)

    # POST
    data, err = parse_json_body(request)
    if err:
        return err

    external_game_id = data.get("external_game_id")
    if not external_game_id or isinstance(external_game_id, int):
        return validation_error({"external_game_id": "Debe ser una cadena de texto"})

    status = data.get("status", LibraryEntry.STATUS_WISHLIST)
    if status not in LibraryEntry.ALLOWED_STATUSES:
        return validation_error({"status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"})

    hours_played = data.get("hours_played", 0)
    if not isinstance(hours_played, int) or hours_played < 0:
        return validation_error({"hours_played": "Debe ser un número entero >= 0"})

    # Caso C: verificar que el juego existe en CheapShark
    try:
        cs_response = requests.get(_CHEAPSHARK_BASE, params={"ids": external_game_id}, timeout=_CHEAPSHARK_TIMEOUT)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        return JsonResponse(
            {"error": "external_service_unavailable", "message": "El catálogo externo no está disponible. Inténtalo más tarde."},
            status=503,
        )
    if cs_response.status_code >= 500:
        return JsonResponse(
            {"error": "external_service_error", "message": "Error al consultar el catálogo externo."},
            status=502,
        )
    try:
        cs_data = cs_response.json()
    except ValueError:
        return JsonResponse(
            {"error": "external_service_error", "message": "Error al consultar el catálogo externo."},
            status=502,
        )
    if not cs_response.ok or not cs_data or external_game_id not in cs_data:
        return JsonResponse(
            {"error": "invalid_external_game_id", "message": "El juego indicado no existe en el catálogo externo.", "details": {"external_game_id": "not_found"}},
            status=400,
        )

    if LibraryEntry.objects.filter(user=request.user, external_game_id=external_game_id).exists():
        return duplicate_entry_error("external_game_id", external_game_id)

    try:
        entry = LibraryEntry.objects.create(
            user=request.user,
            external_game_id=external_game_id,
            status=status,
            hours_played=hours_played,
        )
        return JsonResponse(serialize_entry(entry), status=201)
    except Exception as e:
        return validation_error({"server": str(e)})


@require_http_methods(["GET", "PATCH", "PUT"])
@csrf_exempt
def entries_detail(request, entry_id):
    """GET — detalle. PATCH — actualización parcial. PUT — sustitución completa."""
    if not request.user.is_authenticated:
        return unauthorized_error()

    try:
        entry = LibraryEntry.objects.get(id=entry_id, user=request.user)
    except LibraryEntry.DoesNotExist:
        return not_found_error()

    if request.method == "GET":
        return JsonResponse(serialize_entry(entry))

    # PATCH — actualización parcial
    if request.method == "PATCH":
        data, err = parse_json_body(request)
        if err:
            return err

        if not data.keys() & {"status", "hours_played"}:
            return validation_error({"fields": "Debes enviar al menos un campo para actualizar: status, hours_played"})

        allowed_fields = {"status", "hours_played"}
        invalid_fields = set(data.keys()) - allowed_fields
        if invalid_fields:
            return validation_error({"unknown_fields": f"Campos no permitidos: {', '.join(invalid_fields)}"})

        if "status" in data:
            if data["status"] not in LibraryEntry.ALLOWED_STATUSES:
                return validation_error({"status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"})
            entry.status = data["status"]

        if "hours_played" in data:
            if not isinstance(data["hours_played"], int) or data["hours_played"] < 0:
                return validation_error({"hours_played": "Debe ser un número entero >= 0"})
            entry.hours_played = data["hours_played"]

        entry.save()
        return JsonResponse(serialize_entry(entry), status=200)

    # PUT — sustitución completa
    data, err = parse_json_body(request)
    if err:
        return err

    external_game_id = data.get("external_game_id")
    status = data.get("status")
    hours_played = data.get("hours_played")

    if external_game_id is None:
        return validation_error({"external_game_id": "Campo requerido"})
    if status is None:
        return validation_error({"status": "Campo requerido"})
    if hours_played is None:
        return validation_error({"hours_played": "Campo requerido"})

    if not isinstance(external_game_id, str) or not external_game_id.strip():
        return validation_error({"external_game_id": "Debe ser una cadena de texto no vacía"})
    if status not in LibraryEntry.ALLOWED_STATUSES:
        return validation_error({"status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"})
    if not isinstance(hours_played, int) or hours_played < 0:
        return validation_error({"hours_played": "Debe ser un número entero >= 0"})

    entry.external_game_id = external_game_id
    entry.status = status
    entry.hours_played = hours_played
    entry.save()
    return JsonResponse(serialize_entry(entry), status=200)


# ===== CATALOG ENDPOINTS =====

@require_GET
def catalog_search(request):
    """GET /api/catalog/search/?q=mario"""
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"error": "validation_error", "message": "El parámetro 'q' es requerido"}, status=400)

    data, err = _fetch_cheapshark({"title": q})
    if err:
        return err

    games = [
        {
            "external_game_id": game["gameID"],
            "title": game["external"],
            "thumb": game["thumb"],
        }
        for game in data
    ]
    return JsonResponse(games, safe=False)


@require_http_methods(["POST"])
@csrf_exempt
def catalog_resolve(request):
    """POST /api/catalog/resolve/"""
    data, err = parse_json_body(request)
    if err:
        return err

    ids = data.get("external_game_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i.strip() for i in ids):
        return validation_error({"external_game_ids": "Debe ser una lista de strings no vacía"})

    result, err = _fetch_cheapshark({"ids": ",".join(ids)})
    if err:
        return err

    games = [
        {
            "external_game_id": game_id,
            "title": info["info"]["title"],
            "thumb": info["info"]["thumb"],
        }
        for game_id, info in result.items()
    ]
    return JsonResponse(games, safe=False)


@require_GET
def catalog_by_ids(request):
    """GET /api/catalog/games/?ids=612,627 — consultar varios juegos por gameID."""
    ids_param = request.GET.get("ids", "").strip()
    if not ids_param:
        return JsonResponse({"error": "validation_error", "message": "El parámetro 'ids' es requerido"}, status=400)

    data, err = _fetch_cheapshark({"ids": ids_param})
    if err:
        return err

    games = [
        {
            "id": game_id,
            "title": info["info"]["title"],
            "thumbnail": info["info"]["thumb"],
        }
        for game_id, info in data.items()
    ]
    return JsonResponse(games, safe=False)


@csrf_exempt
@require_POST
def debug_email_test(request):
    if not settings.DEBUG:
        return JsonResponse({"error": "not_found"}, status=404)

    data, err = parse_json_body(request)
    if err:
        return err

    to = data.get("to")
    subject = data.get("subject")
    text = data.get("text")

    if not isinstance(to, str) or not to.strip():
        return validation_error({"to": "Requerido y debe ser texto"})
    if not isinstance(subject, str) or not subject.strip():
        return validation_error({"subject": "Requerido y debe ser texto"})
    if not isinstance(text, str) or not text.strip():
        return validation_error({"text": "Requerido y debe ser texto"})

    try:
        EmailService().send_email(to=to, subject=subject, text=text)
        return JsonResponse({"ok": True})
    except ExternalServiceUnavailable:
        return JsonResponse({"error": "external_service_unavailable"}, status=503)
    except ExternalServiceError:
        return JsonResponse({"error": "external_service_error"}, status=502)
