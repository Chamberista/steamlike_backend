import requests
from django.core.cache import cache

_CHEAPSHARK_BASE = "https://www.cheapshark.com/api/1.0/games"
_CHEAPSHARK_TIMEOUT = 8
_SEARCH_CACHE_PREFIX = "catalog:search"
_SEARCH_CACHE_TTL = 60 * 10  # 10 minutos


class CatalogServiceError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


def _fetch(params):
    try:
        response = requests.get(_CHEAPSHARK_BASE, params=params, timeout=_CHEAPSHARK_TIMEOUT)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise CatalogServiceError("El catálogo externo no está disponible. Inténtalo más tarde.", 503)
    if not response.ok:
        raise CatalogServiceError("Error al consultar el catálogo externo.", 502)
    try:
        return response.json()
    except ValueError:
        raise CatalogServiceError("Error al consultar el catálogo externo.", 502)


def search(q):
    cache_key = f"{_SEARCH_CACHE_PREFIX}:{q.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    data = _fetch({"title": q})
    games = [
        {"external_game_id": g["gameID"], "title": g["external"], "thumb": g["thumb"]}
        for g in data
    ]
    cache.set(cache_key, games, timeout=_SEARCH_CACHE_TTL)
    return games


def resolve(ids):
    data = _fetch({"ids": ",".join(ids)})
    return [
        {"external_game_id": gid, "title": info["info"]["title"], "thumb": info["info"]["thumb"]}
        for gid, info in data.items()
    ]


def verify_game_exists(external_game_id):
    """Devuelve True si el juego existe, False si no. Lanza CatalogServiceError si falla la llamada."""
    data = _fetch({"ids": external_game_id})
    return bool(data) and external_game_id in data


def by_ids(ids_param):
    data = _fetch({"ids": ids_param})
    return [
        {"id": gid, "title": info["info"]["title"], "thumbnail": info["info"]["thumb"]}
        for gid, info in data.items()
    ]
