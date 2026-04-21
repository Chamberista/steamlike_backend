import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.contrib.auth import get_user_model, authenticate, login
from .models import LibraryEntry

User = get_user_model()

# ===== FUNCIONES AUXILIARES =====

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

# ===== AUTH ENDPOINTS =====

@require_http_methods(["POST"])
@csrf_exempt
def register(request):
    """
    POST /api/auth/register/
    Registra un nuevo usuario en la plataforma
    
    Validaciones:
    - JSON válido
    - Body no vacío
    - username y password presentes y son strings
    - username no existe ya
    - password mínimo 8 caracteres
    
    Respuestas:
    - 201: Usuario creado exitosamente
    - 400: Error de validación
    """
    
    try:
        # Parsear JSON del body
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return validation_error({"body": "JSON inválido"})
    
    # Validar que el body no está vacío
    if not data:
        return validation_error({"body": "Body vacío"})
    
    # Obtener campos del JSON
    username = data.get("username")
    password = data.get("password")
    
    # ===== VALIDACIÓN: username existe =====
    if username is None:
        return validation_error({"username": "Campo requerido"})
    
    # ===== VALIDACIÓN: password existe =====
    if password is None:
        return validation_error({"password": "Campo requerido"})
    
    # ===== VALIDACIÓN: username es string =====
    if not isinstance(username, str):
        return validation_error({"username": "Debe ser texto"})
    
    # ===== VALIDACIÓN: password es string =====
    if not isinstance(password, str):
        return validation_error({"password": "Debe ser texto"})
    
    # ===== VALIDACIÓN: username no está vacío =====
    if not username.strip():
        return validation_error({"username": "No puede estar vacío"})
    
    # ===== VALIDACIÓN: password mínimo 8 caracteres =====
    if len(password) < 8:
        return validation_error({"password": "Mínimo 8 caracteres"})
    
    # ===== VALIDACIÓN: username no existe ya =====
    if User.objects.filter(username=username).exists():
        return validation_error({"username": "Ya existe"})
    
    # ===== CREAR USUARIO =====
    try:
        user = User.objects.create_user(
            username=username,
            password=password
        )
        
        # ===== RESPUESTA EXITOSA =====
        # Devuelve id y username, NUNCA la contraseña
        return JsonResponse({
            "id": user.id,
            "username": user.username
        }, status=201)
    
    except Exception as e:
        return validation_error({"server": str(e)})

@require_http_methods(["POST"])
@csrf_exempt
def login_view(request):
    """POST /api/auth/login/"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return validation_error({"body": "JSON inválido"})

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
        return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)
    return JsonResponse({"id": request.user.id, "username": request.user.username}, status=200)


@require_http_methods(["POST"])
@csrf_exempt
def change_password(request):
    """POST /api/users/me/password/"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return validation_error({"body": "JSON inválido"})

    if not data:
        return validation_error({"body": "Body vacío"})

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
    """GET /api/health/ - Health check"""
    return JsonResponse({"status": "ok"})

@csrf_exempt
def entries(request):
    """Maneja GET (listar) y POST (crear) - Solo del usuario autenticado"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)

    if request.method == "GET":
        # Listar SOLO las entradas del usuario actual
        user_entries = LibraryEntry.objects.filter(user=request.user)
        
        data = [
            {
                "id": entry.id,
                "external_game_id": entry.external_game_id,
                "status": entry.status,
                "hours_played": entry.hours_played
            }
            for entry in user_entries
        ]
        
        return JsonResponse(data, safe=False)
    
    elif request.method == "POST":
        # Crear una entrada
        try:
            data = json.loads(request.body)
            
            if not data:
                return validation_error({"body": "Body vacío"})
            
            external_game_id = data.get("external_game_id")
            if not external_game_id or isinstance(external_game_id, int):
                return validation_error({"external_game_id": "Debe ser una cadena de texto"})
            
            status = data.get("status", LibraryEntry.STATUS_WISHLIST)
            if status not in LibraryEntry.ALLOWED_STATUSES:
                return validation_error({
                    "status": f"Debe ser uno de: {', '.join(LibraryEntry.ALLOWED_STATUSES)}"
                })
            
            hours_played = data.get("hours_played", 0)
            if not isinstance(hours_played, int) or hours_played < 0:
                return validation_error({"hours_played": "Debe ser un número entero >= 0"})
            
            if LibraryEntry.objects.filter(user=request.user, external_game_id=external_game_id).exists():
                return duplicate_entry_error("external_game_id", external_game_id)

            try:
                # IMPORTANTE: Asignar el usuario actual
                entry = LibraryEntry.objects.create(
                    user=request.user,
                    external_game_id=external_game_id,
                    status=status,
                    hours_played=hours_played
                ) 
            except Exception as e:
                return validation_error({"server": str(e)})
            
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

@require_http_methods(["GET", "PATCH"])
@csrf_exempt
def entries_detail(request, entry_id):
    """GET: obtiene una entrada. PATCH: actualiza una entrada"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "unauthorized", "message": "No autenticado"}, status=401)

    try:
        # Validar que la entrada existe Y pertenece al usuario actual
        try:
            entry = LibraryEntry.objects.get(id=entry_id, user=request.user)
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