"""geo.admin.ch REST client.

Thin async wrapper over the federal geodata API (``api3.geo.admin.ch``) and the
swisstopo reframe service (``geodesy.geo.admin.ch``). Responsibilities:

- an **egress allow-list** so the server can only ever talk to geo.admin.ch,
- **retry with exponential backoff** for transient transport / 5xx / 429 errors,
- **normalisation** of the two documented upstream quirks: the height and
  reframe services return numbers as JSON *strings*, and the legend endpoint
  serves *HTML* rather than JSON.

Response shapes were verified against the live API (probe 2026-07-24, re-checked
2026-07-25); see the tests for faithful fixtures.
"""

from __future__ import annotations

import asyncio
import html
import json
import re
from urllib.parse import urlparse

import httpx

API_BASE = "https://api3.geo.admin.ch/rest/services"
REFRAME_BASE = "https://geodesy.geo.admin.ch/reframe"

# Egress allow-list. The server must only ever talk to these two hosts.
ALLOWED_HOSTS = frozenset({"api3.geo.admin.ch", "geodesy.geo.admin.ch"})

# Default swissBOUNDARIES3D municipality layer (polygon fill).
MUNICIPALITY_LAYER = "ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill"
# Harmonised building-zones layer published by ARE.
ZONING_LAYER = "ch.are.bauzonen"

_MAX_RETRIES = 2
_BACKOFF_BASE = 0.5  # seconds; 0.5, 1.0 — kept short so tools stay responsive
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class GeoAdminError(Exception):
    """Raised when geo.admin.ch cannot fulfil a request."""


def _assert_host_allowed(url: str) -> None:
    """Reject any URL whose host is not in ALLOWED_HOSTS (defense-in-depth)."""
    host = urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        raise GeoAdminError(f"Host not in allow-list: {host!r}")


def html_to_text(raw: str) -> str:
    """Strip tags and collapse whitespace — legend endpoints serve HTML."""
    text = _TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def _to_float(value: object) -> float:
    """Coerce an upstream value to float; height/reframe return JSON strings."""
    if isinstance(value, str):
        value = value.strip()
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise GeoAdminError(f"Expected a numeric value, got {value!r}") from exc


class GeoAdminClient:
    """Async client for the geo.admin.ch REST services."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def _get(self, url: str, params: dict | None = None) -> httpx.Response:
        _assert_host_allowed(url)
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await self._http.get(url, params=params)
                if response.status_code in _RETRYABLE_STATUS:
                    response.raise_for_status()
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt == _MAX_RETRIES:
                    break
                await asyncio.sleep(_BACKOFF_BASE * (2**attempt))
        raise GeoAdminError(f"geo.admin.ch request failed: {url}") from last_exc

    async def _get_json(self, url: str, params: dict | None = None) -> object:
        response = await self._get(url, params)
        response.raise_for_status()
        return response.json()

    # -- discovery ---------------------------------------------------------

    async def search_layers(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search the layer catalogue (SearchServer, type=layers)."""
        url = f"{API_BASE}/api/SearchServer"
        params = {"searchText": query, "type": "layers", "lang": "de"}
        data = await self._get_json(url, params)
        results = data.get("results", []) if isinstance(data, dict) else []
        out: list[dict] = []
        for r in results[:limit]:
            attrs = r.get("attrs", {})
            out.append(
                {
                    "layer_id": attrs.get("layer"),
                    "label": html_to_text(attrs.get("label", "")),
                    "detail": attrs.get("detail"),
                }
            )
        return out

    async def layer_fields(self, layer: str) -> dict:
        """Return the queryable fields of a layer (api MapServer metadata)."""
        url = f"{API_BASE}/api/MapServer/{layer}"
        data = await self._get_json(url)
        if not isinstance(data, dict):
            raise GeoAdminError(f"Unexpected layer metadata for {layer!r}")
        fields = [
            {
                "name": f.get("name"),
                "type": f.get("type"),
                "example_values": f.get("values", [])[:10],
            }
            for f in data.get("fields", [])
        ]
        return {"layer_id": data.get("id", layer), "name": data.get("name"), "fields": fields}

    async def legend_text(self, layer: str) -> str:
        """Fetch a layer legend (HTML) and reduce it to plain text."""
        url = f"{API_BASE}/all/MapServer/{layer}/legend"
        response = await self._get(url, {"lang": "de"})
        response.raise_for_status()
        return html_to_text(response.text)

    # -- spatial queries ---------------------------------------------------

    async def identify(
        self, layer: str, easting: float, northing: float, tolerance: int = 0, limit: int = 10
    ) -> list[dict]:
        """MapServer identify at an LV95 point. Empty list = soft miss."""
        url = f"{API_BASE}/all/MapServer/identify"
        params = {
            "geometry": f"{easting},{northing}",
            "geometryType": "esriGeometryPoint",
            "layers": f"all:{layer}",
            "mapExtent": "0,0,100,100",
            "imageDisplay": "100,100,96",
            "tolerance": tolerance,
            "sr": 2056,
            "lang": "de",
            "returnGeometry": "false",
        }
        data = await self._get_json(url, params)
        results = data.get("results", []) if isinstance(data, dict) else []
        return results[:limit]

    async def find(
        self, layer: str, search_field: str, search_text: str, limit: int = 10
    ) -> list[dict]:
        """MapServer find — features of a layer by attribute value."""
        url = f"{API_BASE}/all/MapServer/find"
        params = {
            "layer": layer,
            "searchField": search_field,
            "searchText": search_text,
            "sr": 2056,
            "returnGeometry": "false",
            "lang": "de",
        }
        data = await self._get_json(url, params)
        results = data.get("results", []) if isinstance(data, dict) else []
        return results[:limit]

    async def height(self, easting: float, northing: float) -> float:
        """Terrain height at an LV95 point (swissALTI3D). Value arrives as str."""
        url = f"{API_BASE}/height"
        params = {"easting": easting, "northing": northing, "sr": 2056}
        data = await self._get_json(url, params)
        if not isinstance(data, dict) or "height" not in data:
            raise GeoAdminError("Height service returned no 'height' value.")
        return _to_float(data["height"])

    async def profile(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        nb_points: int = 10,
    ) -> list[dict]:
        """Elevation profile along the line start→end (profile.json)."""
        geom = json.dumps(
            {"type": "LineString", "coordinates": [list(start), list(end)]},
            separators=(",", ":"),
        )
        url = f"{API_BASE}/profile.json"
        params = {"geom": geom, "sr": 2056, "nb_points": nb_points}
        data = await self._get_json(url, params)
        if not isinstance(data, list):
            raise GeoAdminError("Profile service returned an unexpected payload.")
        return [
            {
                "distance_m": p.get("dist"),
                "easting": p.get("easting"),
                "northing": p.get("northing"),
                "altitude_m": (p.get("alts") or {}).get("COMB"),
            }
            for p in data
        ]

    async def reframe(self, easting: float, northing: float, direction: str) -> tuple[float, float]:
        """Convert coordinates via the swisstopo reframe service.

        ``direction`` is ``wgs84_to_lv95`` (easting=lon, northing=lat) or
        ``lv95_to_wgs84``. Reframe returns coordinates as JSON strings.
        """
        endpoint = {
            "wgs84_to_lv95": "wgs84tolv95",
            "lv95_to_wgs84": "lv95towgs84",
        }.get(direction)
        if endpoint is None:
            raise GeoAdminError(f"Unknown conversion direction: {direction!r}")
        url = f"{REFRAME_BASE}/{endpoint}"
        params = {"easting": easting, "northing": northing, "format": "json"}
        data = await self._get_json(url, params)
        if not isinstance(data, dict) or "easting" not in data or "northing" not in data:
            raise GeoAdminError("Reframe service returned no coordinates.")
        return _to_float(data["easting"]), _to_float(data["northing"])
