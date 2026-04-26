import json
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterValidTests(TestCase):

    def test_register_valid_returns_201_with_id_and_username(self):
        # Precondiciones
        payload = {"username": "testuser", "password": "password123"}

        # Llamada
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("username", data)
        self.assertEqual(data["username"], "testuser")
        self.assertNotIn("password", data)


class RegisterInvalidTests(TestCase):

    def test_register_empty_json_returns_400(self):
        # Precondiciones: body vacío {}
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_register_missing_password_returns_400(self):
        # Precondiciones: falta el campo password
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"username": "testuser"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_register_missing_username_returns_400(self):
        # Precondiciones: falta el campo username
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_register_short_password_returns_400(self):
        # Precondiciones: contraseña de menos de 8 caracteres
        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"username": "testuser", "password": "short"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_register_duplicate_username_returns_400(self):
        # Precondiciones: usuario ya existe en la base de datos
        User.objects.create_user(username="testuser", password="password123")

        response = self.client.post(
            "/api/auth/register/",
            data=json.dumps({"username": "testuser", "password": "otherpassword"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")


class MeTests(TestCase):

    def test_me_without_login_returns_401(self):
        # Precondiciones: sin autenticar

        # Llamada
        response = self.client.get("/api/users/me/")

        # Comprobaciones
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")
        self.assertEqual(response.json()["message"], "No autenticado")

    def test_me_after_login_returns_200_with_id_and_username(self):
        # Precondiciones: usuario creado y sesión iniciada
        User.objects.create_user(username="testuser", password="password123")
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "testuser", "password": "password123"}),
            content_type="application/json",
        )

        # Llamada
        response = self.client.get("/api/users/me/")

        # Comprobaciones
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("username", data)
        self.assertEqual(data["username"], "testuser")
        self.assertNotIn("password", data)


class LoginValidTests(TestCase):

    def test_login_valid_returns_200(self):
        # Precondiciones: usuario existente
        User.objects.create_user(username="testuser", password="password123")
        payload = {"username": "testuser", "password": "password123"}

        # Llamada
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("username", data)
        self.assertEqual(data["username"], "testuser")
        self.assertNotIn("password", data)


class LoginInvalidTests(TestCase):

    def test_login_wrong_password_returns_401(self):
        # Precondiciones: usuario existe pero contraseña incorrecta
        User.objects.create_user(username="testuser", password="password123")

        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "testuser", "password": "wrongpassword"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")
        self.assertEqual(response.json()["message"], "Credenciales incorrectas")

    def test_login_nonexistent_user_returns_401(self):
        # Precondiciones: usuario que no existe
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "noexiste", "password": "password123"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "unauthorized")

    def test_login_empty_json_returns_400(self):
        # Precondiciones: body vacío {}
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_login_missing_password_returns_400(self):
        # Precondiciones: falta el campo password
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "testuser"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")

    def test_login_missing_username_returns_400(self):
        # Precondiciones: falta el campo username
        response = self.client.post(
            "/api/auth/login/",
            data=json.dumps({"password": "password123"}),
            content_type="application/json",
        )

        # Comprobaciones
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "validation_error")


class LibraryEntryExternalIdLengthTests(TestCase):
    def test_health(self):
        # Precondiciones

        # Llamada (usando self.client y la ruta de la vista que queremos probar)
        response = self.client.get("/api/health/")

        # Comprobaciones
        # Comprobar el código HTTP que devuelve una vista
        self.assertEqual(response.status_code, 200)
        # Comprobar el contenido de la respuesta
        self.assertEqual(response.json(), {"status": "ok"})
        # Verifica que una clave existe dentro del JSON de la respuesta.
        self.assertIn("status", response.json())
        # Comprueba el valor concreto devuelto por la vista.
        self.assertEqual(response.json()["status"], "ok")
        # Asegura que la respuesta no contiene información que no debería aparecer.
        self.assertNotIn("paco", response.json())


class HealthEndpointInvalidMethodTests(TestCase):
    def test_health_post_returns_405(self):
        """POST /api/health/ no es válido y debe devolver 405 Method Not Allowed"""
        response = self.client.post("/api/health/")
        self.assertEqual(response.status_code, 405)


class LibraryEntriesListTests(TestCase):

    def test_entries_without_auth_returns_401(self):
        # Precondiciones: sin autenticar
        response = self.client.get("/api/library/entries/")

        # Comprobaciones
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "No autenticado")

    def test_entries_authenticated_returns_200(self):
        # Precondiciones: usuario creado y sesión iniciada
        User.objects.create_user(username="testuser", password="password123")
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "testuser", "password": "password123"}),
            content_type="application/json",
        )

        # Llamada
        response = self.client.get("/api/library/entries/")

        # Comprobaciones
        self.assertEqual(response.status_code, 200)

    def test_entries_each_user_sees_only_own_entries(self):
        # Precondiciones: dos usuarios con entradas propias
        user1 = User.objects.create_user(username="user1", password="password123")
        user2 = User.objects.create_user(username="user2", password="password123")

        from library.models import LibraryEntry
        LibraryEntry.objects.create(user=user1, external_game_id="game1", status="playing")
        LibraryEntry.objects.create(user=user2, external_game_id="game2", status="wishlist")

        # user1 ve solo su entrada
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "user1", "password": "password123"}),
            content_type="application/json",
        )
        response = self.client.get("/api/library/entries/")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["external_game_id"], "game1")

        # user2 ve solo su entrada
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": "user2", "password": "password123"}),
            content_type="application/json",
        )
        response = self.client.get("/api/library/entries/")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["external_game_id"], "game2")


class LibraryEntryDetailTests(TestCase):

    def _login(self, username, password="password123"):
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
        )

    def test_entry_detail_without_auth_returns_401(self):
        # Precondiciones: entrada existente, sin autenticar
        from library.models import LibraryEntry
        user = User.objects.create_user(username="owner", password="password123")
        entry = LibraryEntry.objects.create(user=user, external_game_id="game1", status="playing")

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "No autenticado")

    def test_entry_detail_own_entry_returns_200(self):
        # Precondiciones: usuario autenticado pide su propia entrada
        from library.models import LibraryEntry
        user = User.objects.create_user(username="owner", password="password123")
        entry = LibraryEntry.objects.create(user=user, external_game_id="game1", status="playing")
        self._login("owner")

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 200)

    def test_entry_detail_other_user_entry_returns_404(self):
        # Precondiciones: dos usuarios, uno pide la entrada del otro
        from library.models import LibraryEntry
        owner = User.objects.create_user(username="owner", password="password123")
        User.objects.create_user(username="other", password="password123")
        entry = LibraryEntry.objects.create(user=owner, external_game_id="game1", status="playing")
        self._login("other")

        response = self.client.get(f"/api/library/entries/{entry.id}/")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "La entrada solicitada no existe")


class LibraryEntryCreateTests(TestCase):

    def _login(self, username, password="password123"):
        self.client.post(
            "/api/auth/login/",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
        )

    def test_create_entry_without_auth_returns_401(self):
        # Precondiciones: sin autenticar
        payload = {"external_game_id": "game1", "status": "playing"}

        response = self.client.post(
            "/api/library/entries/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "No autenticado")

    def test_create_entry_authenticated_returns_201(self):
        # Precondiciones: usuario autenticado
        User.objects.create_user(username="testuser", password="password123")
        self._login("testuser")
        payload = {"external_game_id": "game1", "status": "playing"}

        response = self.client.post(
            "/api/library/entries/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

    def test_create_entry_isolation_between_users(self):
        # Precondiciones: dos usuarios, cada uno crea su entrada
        User.objects.create_user(username="user1", password="password123")
        User.objects.create_user(username="user2", password="password123")

        self._login("user1")
        self.client.post(
            "/api/library/entries/",
            data=json.dumps({"external_game_id": "game1", "status": "playing"}),
            content_type="application/json",
        )

        self._login("user2")
        self.client.post(
            "/api/library/entries/",
            data=json.dumps({"external_game_id": "game2", "status": "wishlist"}),
            content_type="application/json",
        )

        # user1 no ve la entrada de user2
        self._login("user1")
        response = self.client.get("/api/library/entries/")
        ids = [e["external_game_id"] for e in response.json()]
        self.assertIn("game1", ids)
        self.assertNotIn("game2", ids)