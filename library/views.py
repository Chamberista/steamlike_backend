from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate, login
from .models import LibraryEntry
from .utils import (
    validation_error, unauthorized_error, not_found_error,
    duplicate_entry_error, parse_json_body, serialize_entry,
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

    if username is None:
        return validation_error({"username": "Campo requerido"})
    if password is None:
        return validation_error({"password": "Campo requerido"})
    if not isinstance(username, str):
        return validation_error({"username": "Debe ser texto"})
    if not isinstance(password, str):
        return validation_error({"password": "Debe ser texto"})
    if not username.strip():
        return validation_error({"username": "No puede estar vacío"})
    if len(password) < 8:
        return validation_error({"password": "Mínimo 8 caracteres"})
    if User.objects.filter(username=username).exists():
        return validation_error({"username": "Ya existe"})

    try:
        user = User.objects.create_user(username=username, password=password)
        return JsonResponse({"id": user.id, "username": user.username}, status=201)
    except Exception as e:
        return validation_error({"server": str(e)})


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


@require_http_methods(["GET", "PATCH"])
@csrf_exempt
def entries_detail(request, entry_id):
    """GET /api/library/entries/<id>/ — detalle. PATCH — actualizar."""
    if not request.user.is_authenticated:
        return unauthorized_error()

    try:
        entry = LibraryEntry.objects.get(id=entry_id, user=request.user)
    except LibraryEntry.DoesNotExist:
        return not_found_error()

    if request.method == "GET":
        return JsonResponse(serialize_entry(entry))

    # PATCH
    data, err = parse_json_body(request)
    if err:
        return err

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
