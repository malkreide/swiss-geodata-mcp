"""
swiss-geodata-mcp — FastMCP server for the Swiss federal geodata (geo.admin.ch).

Nine read-only ``geo_*`` tools over the federal geodata infrastructure: layer
discovery, spatial identify/find, municipality and building-zone lookup, terrain
heights and elevation profiles, layer metadata, and WGS84↔LV95 conversion.

Architecture A (live-API-only): every response is fetched from upstream and
carries ``provenance: live_api``. All coordinates are LV95 (EPSG:2056) unless a
tool explicitly documents otherwise.
"""

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from swiss_geodata_mcp.geoadmin import (
    MUNICIPALITY_LAYER,
    ZONING_LAYER,
    GeoAdminClient,
    GeoAdminError,
)
from swiss_geodata_mcp.models import GeoEnvelope

# stdio-transport MCP servers must keep stdout reserved for the JSON-RPC
# stream — every log line goes to stderr.
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("swiss_geodata_mcp")

DEFAULT_TIMEOUT = 20.0

# Plausible LV95 (EPSG:2056) extent for Switzerland, with a small margin. Used
# to fail fast on WGS84 input (e.g. 8.54, 47.37) with a pointer to the
# conversion tool.
LV95_EAST_MIN, LV95_EAST_MAX = 2_450_000, 2_850_000
LV95_NORTH_MIN, LV95_NORTH_MAX = 1_060_000, 1_310_000


def _lv95_error(easting: float, northing: float) -> str | None:
    """Return an actionable error string if the point is not plausible LV95."""
    if LV95_EAST_MIN <= easting <= LV95_EAST_MAX and LV95_NORTH_MIN <= northing <= LV95_NORTH_MAX:
        return None
    return (
        f"Coordinates ({easting}, {northing}) are not plausible LV95 (EPSG:2056). "
        "LV95 easting is ~2.485–2.834 M and northing ~1.075–1.296 M. If you have "
        "WGS84 lon/lat, convert first with geo_convert_coordinates "
        "(direction='wgs84_to_lv95')."
    )


# ---------------------------------------------------------------------------
# Shared client (managed via FastMCP lifespan)
# ---------------------------------------------------------------------------


class _Runtime:
    http: httpx.AsyncClient | None = None
    client: GeoAdminClient | None = None


_runtime = _Runtime()


def _client() -> GeoAdminClient:
    client = _runtime.client
    if client is None:
        raise RuntimeError(
            "GeoAdminClient not initialised — _lifespan did not run. This usually "
            "means the server was started without going through FastMCP.run()."
        )
    return client


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Open one httpx.AsyncClient / GeoAdminClient for the whole server lifetime."""
    _runtime.http = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    _runtime.client = GeoAdminClient(_runtime.http)
    try:
        yield
    finally:
        await _runtime.http.aclose()
        _runtime.http = None
        _runtime.client = None


mcp = FastMCP(
    "swiss_geodata_mcp",
    instructions=(
        "MCP server for the Swiss federal geodata infrastructure (geo.admin.ch). "
        "Discover ~700 layers by keyword (geo_search_layers), inspect a layer's "
        "queryable fields (geo_layer_info), and query points: geo_identify / "
        "geo_find for any layer, geo_municipality_at (municipality + BFS number + "
        "canton), geo_zoning_at (harmonised ARE building zones), geo_height and "
        "geo_elevation_profile (swissALTI3D), and geo_convert_coordinates "
        "(WGS84 ↔ LV95). All coordinates are LV95 (EPSG:2056) unless noted. "
        "Read-only, no authentication required."
    ),
    # Bind to loopback by default (SEC-016 / NeighborJack): the HTTP transports
    # must not expose all interfaces unless a deployment explicitly opts in by
    # setting HOST=0.0.0.0. stdio (the default transport) does not bind at all.
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000")),
    lifespan=_lifespan,
)


def _handle_error(e: Exception) -> str:
    """Reduce any failure to a clear, sanitised message for the model.

    Full details go to stderr (server-side only); the LLM sees a generic string
    so upstream bodies, URLs and stack-trace fragments don't leak into context.
    """
    if isinstance(e, GeoAdminError):
        return f"Error: {e}"
    if isinstance(e, httpx.HTTPStatusError):
        return f"Error: geo.admin.ch returned HTTP {e.response.status_code}."
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request to geo.admin.ch timed out. Please try again."
    if isinstance(e, httpx.ConnectError):
        return "Error: Cannot reach geo.admin.ch. Check network connectivity."
    logger.exception("Unhandled error while calling the geo.admin.ch API")
    return "Error: Unexpected error processing the request. See server log for details."


_READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class Direction(StrEnum):
    WGS84_TO_LV95 = "wgs84_to_lv95"
    LV95_TO_WGS84 = "lv95_to_wgs84"


class SearchLayersInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    query: str = Field(
        description="Keyword(s) to search the layer catalogue, e.g. 'lärm'.", min_length=1
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum layers to return.")


class PointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    easting: float = Field(description="LV95 easting (E), e.g. 2683531.")
    northing: float = Field(description="LV95 northing (N), e.g. 1247914.")


class IdentifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    layer: str = Field(
        description="Layer id, e.g. 'ch.are.bauzonen'. Find ids with geo_search_layers.",
        min_length=1,
    )
    easting: float = Field(description="LV95 easting (E).")
    northing: float = Field(description="LV95 northing (N).")
    tolerance: int = Field(
        default=0,
        ge=0,
        le=50,
        description="Search tolerance in pixels. 0 works for polygon layers.",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum features to return.")


class FindInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    layer: str = Field(description="Layer id to search, e.g. 'ch.are.bauzonen'.", min_length=1)
    search_field: str = Field(
        description="Attribute field to match. See geo_layer_info for a layer's fields.",
        min_length=1,
    )
    search_text: str = Field(
        description="Value to match in search_field, e.g. 'Zürich'.", min_length=1
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum features to return.")


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    easting_start: float = Field(description="LV95 easting of the line start.")
    northing_start: float = Field(description="LV95 northing of the line start.")
    easting_end: float = Field(description="LV95 easting of the line end.")
    northing_end: float = Field(description="LV95 northing of the line end.")
    nb_points: int = Field(
        default=10, ge=2, le=200, description="Number of sample points along the line."
    )


class LayerInfoInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    layer: str = Field(description="Layer id, e.g. 'ch.are.bauzonen'.", min_length=1)


class ConvertInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    easting: float = Field(
        description="Input easting: LV95 E, or WGS84 longitude when converting from WGS84."
    )
    northing: float = Field(
        description="Input northing: LV95 N, or WGS84 latitude when converting from WGS84."
    )
    direction: Direction = Field(
        default=Direction.WGS84_TO_LV95,
        description="'wgs84_to_lv95' (lon/lat → LV95) or 'lv95_to_wgs84'.",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(name="geo_search_layers", annotations={"title": "Search geodata layers", **_READ_ONLY})
async def geo_search_layers(params: SearchLayersInput) -> str:
    """Keyword-search the ~700-layer federal geodata catalogue (geo.admin.ch SearchServer).

    The discovery entry point: returns matching layer ids you can then pass to
    geo_identify, geo_find or geo_layer_info. Data source: geo.admin.ch SearchServer.
    """
    try:
        results = await _client().search_layers(params.query, params.limit)
        return GeoEnvelope(
            source="geo.admin.ch SearchServer",
            query={"query": params.query, "limit": params.limit},
            result=results,
            note=None if results else "No layers matched — try a broader or German keyword.",
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="geo_identify", annotations={"title": "Identify features at a point", **_READ_ONLY})
async def geo_identify(params: IdentifyInput) -> str:
    """What is at this LV95 point on a given layer? (geo.admin.ch MapServer identify).

    Returns the feature attributes at the point. An empty result is a soft miss
    (nothing at that location), not an error. Data source: geo.admin.ch MapServer.
    """
    err = _lv95_error(params.easting, params.northing)
    if err:
        return f"Error: {err}"
    try:
        results = await _client().identify(
            params.layer, params.easting, params.northing, params.tolerance, params.limit
        )
        attributes = [r.get("attributes", {}) for r in results]
        return GeoEnvelope(
            source="geo.admin.ch MapServer identify",
            query={"layer": params.layer, "easting": params.easting, "northing": params.northing},
            result=attributes,
            note=None if attributes else "No feature at this point on the given layer (soft miss).",
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="geo_find", annotations={"title": "Find features by attribute", **_READ_ONLY})
async def geo_find(params: FindInput) -> str:
    """Find features on a layer by attribute value (geo.admin.ch MapServer find).

    Use geo_layer_info first to see a layer's queryable fields. Data source:
    geo.admin.ch MapServer.
    """
    try:
        results = await _client().find(
            params.layer, params.search_field, params.search_text, params.limit
        )
        attributes = [r.get("attributes", {}) for r in results]
        return GeoEnvelope(
            source="geo.admin.ch MapServer find",
            query={
                "layer": params.layer,
                "search_field": params.search_field,
                "search_text": params.search_text,
            },
            result=attributes,
            note=None
            if attributes
            else "No features matched — check search_field via geo_layer_info.",
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="geo_municipality_at", annotations={"title": "Municipality at a point", **_READ_ONLY}
)
async def geo_municipality_at(params: PointInput) -> str:
    """Municipality, BFS number and canton containing an LV95 point (swissBOUNDARIES3D).

    The BFS number bridges to the register and statistics servers
    (swiss-housing-mcp, swiss-statistics-mcp). Data source: swissBOUNDARIES3D.
    """
    err = _lv95_error(params.easting, params.northing)
    if err:
        return f"Error: {err}"
    try:
        results = await _client().identify(
            MUNICIPALITY_LAYER, params.easting, params.northing, tolerance=0, limit=200
        )
        # The layer carries one polygon per historical year; keep the current one.
        current = [
            r.get("attributes", {})
            for r in results
            if r.get("attributes", {}).get("is_current_jahr") is True
        ]
        payload = None
        if current:
            a = current[0]
            payload = {
                "municipality": a.get("gemname"),
                "bfs_number": a.get("gde_nr"),
                "canton": a.get("kanton"),
            }
        return GeoEnvelope(
            source="swissBOUNDARIES3D (swisstopo)",
            query={"easting": params.easting, "northing": params.northing},
            result=payload,
            note=None
            if payload
            else "No current municipality at this point (outside CH or on a boundary).",
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="geo_zoning_at", annotations={"title": "Building zone at a point", **_READ_ONLY})
async def geo_zoning_at(params: PointInput) -> str:
    """Harmonised building zone(s) at an LV95 point (ch.are.bauzonen, ARE).

    Returns the harmonised main-use zone type. Data source: ch.are.bauzonen.
    """
    err = _lv95_error(params.easting, params.northing)
    if err:
        return f"Error: {err}"
    try:
        results = await _client().identify(
            ZONING_LAYER, params.easting, params.northing, tolerance=0, limit=10
        )
        zones = [
            {
                "zone_type_de": a.get("ch_bez_d"),
                "zone_type_fr": a.get("ch_bez_f"),
                "code": a.get("ch_code_hn"),
                "municipality": a.get("name"),
                "bfs_number": a.get("bfs_no"),
                "canton": a.get("kt_kz"),
            }
            for a in (r.get("attributes", {}) for r in results)
        ]
        return GeoEnvelope(
            source="ch.are.bauzonen (ARE)",
            query={"easting": params.easting, "northing": params.northing},
            result=zones,
            note=(
                "The harmonised ch.are.bauzonen layer is an ARE synthesis; legally "
                "binding is only the cantonal/communal Nutzungsplanung."
            ),
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="geo_height", annotations={"title": "Terrain height at a point", **_READ_ONLY})
async def geo_height(params: PointInput) -> str:
    """Terrain height (m a.s.l.) at an LV95 point (swissALTI3D height service)."""
    err = _lv95_error(params.easting, params.northing)
    if err:
        return f"Error: {err}"
    try:
        height = await _client().height(params.easting, params.northing)
        return GeoEnvelope(
            source="swissALTI3D height service (swisstopo)",
            query={"easting": params.easting, "northing": params.northing},
            result={"height_m": height},
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="geo_elevation_profile",
    annotations={"title": "Elevation profile along a line", **_READ_ONLY},
)
async def geo_elevation_profile(params: ProfileInput) -> str:
    """Elevation profile along a line between two LV95 points (geo.admin.ch profile service)."""
    for e, n in (
        (params.easting_start, params.northing_start),
        (params.easting_end, params.northing_end),
    ):
        err = _lv95_error(e, n)
        if err:
            return f"Error: {err}"
    try:
        points = await _client().profile(
            (params.easting_start, params.northing_start),
            (params.easting_end, params.northing_end),
            params.nb_points,
        )
        return GeoEnvelope(
            source="geo.admin.ch profile service (swissALTI3D)",
            query={
                "start": [params.easting_start, params.northing_start],
                "end": [params.easting_end, params.northing_end],
                "nb_points": params.nb_points,
            },
            result=points,
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(name="geo_layer_info", annotations={"title": "Layer fields and legend", **_READ_ONLY})
async def geo_layer_info(params: LayerInfoInput) -> str:
    """Queryable fields and legend (plain text) for a layer (geo.admin.ch MapServer).

    Reveals the fields you can pass to geo_find as search_field. Data source:
    geo.admin.ch MapServer.
    """
    try:
        meta = await _client().layer_fields(params.layer)
        try:
            legend = await _client().legend_text(params.layer)
        except Exception:
            legend = None
        meta["legend"] = legend
        return GeoEnvelope(
            source="geo.admin.ch MapServer",
            query={"layer": params.layer},
            result=meta,
        ).to_json()
    except Exception as e:
        return _handle_error(e)


@mcp.tool(
    name="geo_convert_coordinates", annotations={"title": "Convert WGS84 ↔ LV95", **_READ_ONLY}
)
async def geo_convert_coordinates(params: ConvertInput) -> str:
    """Convert coordinates between WGS84 (lon/lat) and LV95 (geodesy.geo.admin.ch reframe).

    For 'wgs84_to_lv95', easting=longitude and northing=latitude. Data source:
    swisstopo reframe service.
    """
    try:
        out_e, out_n = await _client().reframe(
            params.easting, params.northing, params.direction.value
        )
        return GeoEnvelope(
            source="geodesy.geo.admin.ch reframe (swisstopo)",
            query={
                "easting": params.easting,
                "northing": params.northing,
                "direction": params.direction.value,
            },
            result={"easting": out_e, "northing": out_n},
        ).to_json()
    except Exception as e:
        return _handle_error(e)
