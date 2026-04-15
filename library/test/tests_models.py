from django.test import TestCase

from library.models import LibraryEntry

class DemoTest(TestCase):
    def test_demo(self):
        # Comprueba que dos valores son exactamente iguales.
        self.assertEqual(4, 2+2)
        # Comprueba si una condición se cumple o no.
        self.assertTrue(4 == 4)
        self.assertFalse(5 == 4)
        # Permiten distinguir entre None y otros valores como cadenas vacías o ceros.
        self.assertIsNone(None)
        # Comprueba que una acción provoca un error concreto.
        with self.assertRaises(ZeroDivisionError):
            # Codigo que lanza la excepcion
            4/0

class LibraryEntryExternalIdLengthTests(TestCase):
    def test_external_id_length_counts_regular_string(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="abc")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 3)

    def test_external_id_length_counts_empty_string_as_zero(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 0)

    def test_external_id_length_counts_whitespace(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="   ")

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 3)

    def test_external_id_length_counts_max_length_boundary_100(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="x" * 100)

        # Llamada
        longitud = entry.external_id_length()

        # Comprobaciones
        self.assertEqual(longitud, 100)

    def test_external_id_length_raises_type_error_if_not_string_or_none(self):
        # Caso anómalo: asignación indebida en memoria.
        # Precondiciones
        entry = LibraryEntry(external_game_id=123)

        # Llamada
        # Comprobaciones
        with self.assertRaises(TypeError):
            entry.external_id_length()

class LibraryEntryExternalIdUpperTests(TestCase):
    def test_external_id_upper(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="abc")

        # Llamada
        cadena = entry.external_id_upper()

        # Comprobaciones
        self.assertEqual(cadena, "ABC")

    def test_external_id_upper_empty_string(self):
        # Precondiciones
        entry = LibraryEntry(external_game_id="")

        # Llamada
        cadena = entry.external_id_upper()

        # Comprobaciones
        self.assertEqual(cadena, "")

    def test_external_id_upper_mixed_case(self):
        # Precondiciones: ID con mayúsculas y minúsculas mezcladas
        entry = LibraryEntry(external_game_id="AbC123xYz")
        
        # Llamada
        resultado = entry.external_id_upper()
        
        # Comprobaciones
        self.assertEqual(resultado, "ABC123XYZ")

    def test_external_id_upper_converts_number_to_string(self):
        # Precondiciones: ID es un número
        entry = LibraryEntry(external_game_id=12345)
        
        # Llamada
        resultado = entry.external_id_upper()
        
        # Comprobaciones: números se devuelven como string
        self.assertEqual(resultado, "12345")


class LibraryEntryHoursPlayedLabelTests(TestCase):
    """Tests para el método hours_played_label()"""
    
    def test_hours_played_label_returns_none_when_zero(self):
        # Precondiciones: 0 horas jugadas
        entry = LibraryEntry(hours_played=0)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones: debe devolver "none"
        self.assertEqual(label, "none")
    
    def test_hours_played_label_returns_low_when_between_1_and_9(self):
        # Precondiciones: 5 horas jugadas (dentro de rango bajo)
        entry = LibraryEntry(hours_played=5)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones: debe devolver "low"
        self.assertEqual(label, "low")
    
    def test_hours_played_label_returns_low_at_1(self):
        # Precondiciones: límite inferior del rango bajo
        entry = LibraryEntry(hours_played=1)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones
        self.assertEqual(label, "low")
    
    def test_hours_played_label_returns_low_at_9(self):
        # Precondiciones: límite superior del rango bajo
        entry = LibraryEntry(hours_played=9)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones
        self.assertEqual(label, "low")
    
    def test_hours_played_label_returns_high_when_10_or_more(self):
        # Precondiciones: 10 horas jugadas (inicio del rango alto)
        entry = LibraryEntry(hours_played=10)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones: debe devolver "high"
        self.assertEqual(label, "high")
    
    def test_hours_played_label_returns_high_for_large_values(self):
        # Precondiciones: muchas horas jugadas
        entry = LibraryEntry(hours_played=1000)
        
        # Llamada
        label = entry.hours_played_label()
        
        # Comprobaciones
        self.assertEqual(label, "high")

class LibraryEntryStatusValueTests(TestCase):
    """Tests para el método status_value()"""
    
    def test_status_value_returns_0_for_wishlist(self):
        # Precondiciones: status es "wishlist"
        entry = LibraryEntry(status=LibraryEntry.STATUS_WISHLIST)
        
        # Llamada
        valor = entry.status_value()
        
        # Comprobaciones: debe devolver 0
        self.assertEqual(valor, 0)
    
    def test_status_value_returns_1_for_playing(self):
        # Precondiciones: status es "playing"
        entry = LibraryEntry(status=LibraryEntry.STATUS_PLAYING)
        
        # Llamada
        valor = entry.status_value()
        
        # Comprobaciones: debe devolver 1
        self.assertEqual(valor, 1)
    
    def test_status_value_returns_2_for_completed(self):
        # Precondiciones: status es "completed"
        entry = LibraryEntry(status=LibraryEntry.STATUS_COMPLETED)
        
        # Llamada
        valor = entry.status_value()
        
        # Comprobaciones: debe devolver 2
        self.assertEqual(valor, 2)
    
    def test_status_value_returns_3_for_dropped(self):
        # Precondiciones: status es "dropped"
        entry = LibraryEntry(status=LibraryEntry.STATUS_DROPPED)
        
        # Llamada
        valor = entry.status_value()
        
        # Comprobaciones: debe devolver 3
        self.assertEqual(valor, 3)
    
    def test_status_value_returns_minus_1_for_invalid_status(self):
        # Precondiciones: status inválido
        entry = LibraryEntry(status="invalid_status")
        
        # Llamada
        valor = entry.status_value()
        
        # Comprobaciones: debe devolver -1
        self.assertEqual(valor, -1)
    
    def test_status_value_maintains_order(self):
        # Precondiciones: comprobar que el orden es coherente
        wishlist_val = LibraryEntry(status=LibraryEntry.STATUS_WISHLIST).status_value()
        playing_val = LibraryEntry(status=LibraryEntry.STATUS_PLAYING).status_value()
        completed_val = LibraryEntry(status=LibraryEntry.STATUS_COMPLETED).status_value()
        dropped_val = LibraryEntry(status=LibraryEntry.STATUS_DROPPED).status_value()
        
        # Comprobaciones: el orden debe ser creciente
        self.assertLess(wishlist_val, playing_val)
        self.assertLess(playing_val, completed_val)
        self.assertLess(completed_val, dropped_val)

