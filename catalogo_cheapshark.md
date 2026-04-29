# Ejercicio 1 — Integración del Catálogo Externo (CheapShark)

## 1. ¿Qué es el catálogo?

El catálogo es un conjunto de videojuegos que **no pertenece al sistema** y **no se almacena en nuestra base de datos**. En lugar de eso, se consulta bajo demanda a un servicio externo: la API pública de **CheapShark** (`https://www.cheapshark.com/api/1.0/`).

---

## 2. Endpoints relevantes de CheapShark

### 2.1 Buscar juegos por texto

| Campo | Valor |
|---|---|
| **URL** | `GET https://www.cheapshark.com/api/1.0/games` |
| **Parámetro principal** | `title` — texto libre a buscar |
| **Parámetros opcionales** | `limit` (máx. resultados), `exact` (0 o 1, coincidencia exacta) |

**Ejemplo de petición:**
```
GET https://www.cheapshark.com/api/1.0/games?title=batman&limit=10
```

**Ejemplo de respuesta (lista):**
```json
[
  {
    "gameID": "612",
    "steamAppID": "35140",
    "cheapest": "0.99",
    "cheapestDealID": "...",
    "external": "Batman: Arkham Asylum GOTY Edition",
    "internalName": "BATMANARKHAMASYLUMGOTYEDITION",
    "thumb": "https://cdn.cloudflare.steamstatic.com/steam/apps/35140/capsule_sm_120.jpg"
  }
]
```

> El campo `gameID` es el identificador externo que usamos como `external_game_id` en nuestra base de datos.

---

### 2.2 Consultar información de varios juegos por ID

| Campo | Valor |
|---|---|
| **URL** | `GET https://www.cheapshark.com/api/1.0/games` |
| **Parámetro principal** | `ids` — lista de `gameID` separados por comas |

**Ejemplo de petición:**
```
GET https://www.cheapshark.com/api/1.0/games?ids=612,627,628
```

**Ejemplo de respuesta (objeto indexado por gameID):**
```json
{
  "612": {
    "info": {
      "title": "Batman: Arkham Asylum GOTY Edition",
      "steamAppID": "35140",
      "thumb": "https://..."
    },
    "cheapestPriceEver": { "price": "0.49", "date": 1612000000 },
    "deals": [ { "storeID": "1", "dealID": "...", "price": "0.99" } ]
  }
}
```

---

## 3. Autenticación y aspectos relevantes

- **No requiere autenticación**: La API de CheapShark es completamente pública. No hay API key, tokens ni cabeceras especiales.
- **Rate limiting**: No documenta un límite oficial, pero es una API pública con recursos compartidos. Deben evitarse peticiones masivas o en bucle sin control.
- **Solo lectura**: No permite escribir ni modificar datos; únicamente se consulta.
- **Datos de precio, no de juego completo**: CheapShark es un comparador de precios. La información de juego (título, imagen) es secundaria; los datos principales son ofertas y tiendas.

---

## 4. Preguntas de diseño

### ¿Por qué `external_game_id` usa el `gameID` de CheapShark?

El `gameID` de CheapShark es el identificador estable y único que CheapShark asigna a cada juego. Usarlo como `external_game_id` en `LibraryEntry` permite que el backend pueda, en cualquier momento, consultar información actualizada de ese juego sin almacenar nada más.

```
LibraryEntry.external_game_id = "612"
→ GET /api/1.0/games?ids=612
→ Obtener título, imagen, precio actual
```

---

### ¿Por qué al frontend solo se le devuelve información mínima del juego?

El frontend no necesita todos los detalles de ofertas y tiendas que devuelve CheapShark. Devolver solo información mínima (título, imagen, `gameID`) tiene varias ventajas:

1. **Menor payload**: Menos datos transmitidos → respuestas más rápidas.
2. **Desacoplamiento**: Si CheapShark cambia su estructura interna, el contrato con el frontend no se rompe.
3. **Responsabilidad única**: El backend filtra y normaliza; el frontend no necesita conocer la estructura interna de CheapShark.
4. **Privacidad del proveedor**: No se expone directamente la fuente ni su estructura completa.

---

### ¿Por qué el catálogo no se almacena en la base de datos del sistema?

| Razón | Explicación |
|---|---|
| **Datos que no son nuestros** | Los juegos son propiedad de CheapShark/Steam. Almacenarlos sería duplicar datos ajenos y asumir responsabilidad de mantenerlos actualizados. |
| **Información volátil** | Precios, disponibilidad y detalles cambian constantemente. Cualquier copia local quedaría desactualizada al instante. |
| **Escalabilidad** | CheapShark tiene miles de juegos. Importarlos todos supondría un coste innecesario en almacenamiento y tiempo. |
| **Consulta bajo demanda** | Solo se necesitan los datos cuando el usuario los pide. No tiene sentido guardar lo que no se usa. |
| **Separación de responsabilidades** | Nuestra base de datos gestiona el estado del usuario (biblioteca, horas, estado). El catálogo es información de referencia externa. |

---

## 5. Resumen visual del flujo

**Búsqueda por texto:**
```
Frontend
   │  GET /api/catalog/search?title=batman
   ▼
Backend (Django)
   │  GET https://www.cheapshark.com/api/1.0/games?title=batman
   ▼
CheapShark API  →  [ { gameID, external, thumb, cheapest } ]
   ▼
Backend filtra  →  [ { id, title, thumbnail } ]
   ▼
Frontend
```

**Consulta por IDs:**
```
Frontend
   │  GET /api/catalog/games?ids=612,627
   ▼
Backend (Django)
   │  GET https://www.cheapshark.com/api/1.0/games?ids=612,627
   ▼
CheapShark API  →  { "612": { info, deals }, "627": { info, deals } }
   ▼
Backend filtra  →  [ { id, title, thumbnail }, { id, title, thumbnail } ]
   ▼
Frontend
```

---

## 6. Conclusión

CheapShark proporciona dos modos de uso sobre el mismo endpoint `/games` que cubren exactamente las dos necesidades del sistema:

- **`?title=`** → búsqueda por texto libre.
- **`?ids=`** → consulta de varios juegos a la vez por su `gameID`.

No requiere autenticación, es de solo lectura y sus datos son volátiles, lo que justifica que el catálogo no se persista en nuestra base de datos y se consulte únicamente cuando el usuario lo necesita.
