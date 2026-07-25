"""Unit tests for swiss-geodata-mcp.

Fast, network-free, run in CI on every PR. HTTP is intercepted by ``respx``.
Fixtures mirror the shapes returned by the live geo.admin.ch API (probed
2026-07-24, re-checked 2026-07-25). End-to-end coverage against the live API
lives in ``tests/test_live.py`` (marker: ``live``).
"""

import json
import sys
from pathlib import Path

import httpx
import pytest
import respx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from swiss_geodata_mcp.geoadmin import GeoAdminError, _assert_host_allowed, html_to_text
from swiss_geodata_mcp.server import (
    ConvertInput,
    FindInput,
    IdentifyInput,
    LayerInfoInput,
    PointInput,
    ProfileInput,
    SearchLayersInput,
    _lifespan,
    geo_convert_coordinates,
    geo_elevation_profile,
    geo_find,
    geo_height,
    geo_identify,
    geo_layer_info,
    geo_municipality_at,
    geo_search_layers,
    geo_zoning_at,
    mcp,
)

API = "https://api3.geo.admin.ch/rest/services"
REFRAME = "https://geodesy.geo.admin.ch/reframe"
E, N = 2683531, 1247914


@pytest.fixture
async def lifespan_started():
    """Open the shared client via _lifespan for the duration of the test."""
    async with _lifespan(mcp):
        yield


# ---------------------------------------------------------------------------
# Faithful upstream fixtures
# ---------------------------------------------------------------------------


def _search_response() -> dict:
    return {
        "results": [
            {
                "attrs": {
                    "label": "<b>Bauzonen Schweiz (harmonisiert)</b>",
                    "layer": "ch.are.bauzonen",
                    "detail": "bauzonen schweiz harmonisiert",
                },
                "id": 59,
                "weight": 62,
            }
        ]
    }


def _zoning_identify() -> dict:
    return {
        "results": [
            {
                "layerBodId": "ch.are.bauzonen",
                "layerName": "Bauzonen Schweiz (harmonisiert)",
                "featureId": 368499,
                "attributes": {
                    "name": "Zürich",
                    "ch_code_hn": "13",
                    "kt_kz": "ZH",
                    "bfs_no": "261",
                    "ch_bez_f": "Zones mixtes",
                    "ch_bez_d": "Mischzonen",
                    "label": "Zürich",
                },
            }
        ]
    }


def _municipality_identify() -> dict:
    # Two historical polygons + the current one (is_current_jahr True).
    return {
        "results": [
            {
                "attributes": {
                    "gemname": "Zürich",
                    "gde_nr": 253,
                    "kanton": "ZH",
                    "jahr": 1950,
                    "is_current_jahr": False,
                }
            },
            {
                "attributes": {
                    "gemname": "Zürich",
                    "gde_nr": 261,
                    "kanton": "ZH",
                    "jahr": 2026,
                    "is_current_jahr": True,
                }
            },
        ]
    }


def _layer_metadata() -> dict:
    return {
        "id": "ch.are.bauzonen",
        "name": "Bauzonen Schweiz (harmonisiert)",
        "fields": [
            {
                "name": "ch_bez_d",
                "type": "VARCHAR",
                "alias": "ch.are.bauzonen.ch_bez_d",
                "values": ["Mischzonen", "Wohnzonen"],
            },
            {
                "name": "kt_kz",
                "type": "VARCHAR",
                "alias": "ch.are.bauzonen.kt_kz",
                "values": ["ZH", "BE"],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_html_to_text_strips_tags():
    assert html_to_text("<div><b>Bauzonen</b>\n  Schweiz</div>") == "Bauzonen Schweiz"


def test_host_allow_list_rejects_foreign_host():
    with pytest.raises(GeoAdminError):
        _assert_host_allowed("https://evil.example.com/rest/services/height")
    # Allowed hosts do not raise.
    _assert_host_allowed(f"{API}/height")
    _assert_host_allowed(f"{REFRAME}/wgs84tolv95")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@respx.mock
async def test_search_layers_unwraps_and_cleans_label(lifespan_started):
    respx.get(f"{API}/api/SearchServer").mock(
        return_value=httpx.Response(200, json=_search_response())
    )
    out = json.loads(await geo_search_layers(SearchLayersInput(query="bauzonen")))
    assert out["provenance"] == "live_api"
    assert out["result"][0]["layer_id"] == "ch.are.bauzonen"
    assert out["result"][0]["label"] == "Bauzonen Schweiz (harmonisiert)"  # HTML stripped


@respx.mock
async def test_identify_hit_and_soft_miss(lifespan_started):
    route = respx.get(f"{API}/all/MapServer/identify")
    route.mock(return_value=httpx.Response(200, json=_zoning_identify()))
    hit = json.loads(
        await geo_identify(IdentifyInput(layer="ch.are.bauzonen", easting=E, northing=N))
    )
    assert hit["result"][0]["ch_bez_d"] == "Mischzonen"

    route.mock(return_value=httpx.Response(200, json={"results": []}))
    miss = json.loads(
        await geo_identify(IdentifyInput(layer="ch.are.bauzonen", easting=E, northing=N))
    )
    assert miss["result"] == []
    assert "soft miss" in miss["note"]


async def test_identify_rejects_wgs84_coordinates(lifespan_started):
    # WGS84 lon/lat (8.54, 47.37) is implausible LV95 — fail fast, no HTTP call.
    out = await geo_identify(IdentifyInput(layer="ch.are.bauzonen", easting=8.54, northing=47.37))
    assert out.startswith("Error:")
    assert "geo_convert_coordinates" in out


@respx.mock
async def test_zoning_at_includes_legal_note(lifespan_started):
    respx.get(f"{API}/all/MapServer/identify").mock(
        return_value=httpx.Response(200, json=_zoning_identify())
    )
    out = json.loads(await geo_zoning_at(PointInput(easting=E, northing=N)))
    assert out["result"][0]["zone_type_de"] == "Mischzonen"
    assert out["result"][0]["bfs_number"] == "261"
    assert "Nutzungsplanung" in out["note"]


@respx.mock
async def test_municipality_at_picks_current_year(lifespan_started):
    respx.get(f"{API}/all/MapServer/identify").mock(
        return_value=httpx.Response(200, json=_municipality_identify())
    )
    out = json.loads(await geo_municipality_at(PointInput(easting=E, northing=N)))
    assert out["result"]["bfs_number"] == 261  # current record, not the 1950 one
    assert out["result"]["municipality"] == "Zürich"
    assert out["result"]["canton"] == "ZH"


@respx.mock
async def test_find_returns_attributes(lifespan_started):
    respx.get(f"{API}/all/MapServer/find").mock(
        return_value=httpx.Response(200, json=_zoning_identify())
    )
    out = json.loads(
        await geo_find(
            FindInput(layer="ch.are.bauzonen", search_field="name", search_text="Zürich")
        )
    )
    assert out["result"][0]["name"] == "Zürich"


@respx.mock
async def test_height_parses_string_value(lifespan_started):
    # The height service returns the value as a JSON *string*.
    respx.get(f"{API}/height").mock(return_value=httpx.Response(200, json={"height": "411.1"}))
    out = json.loads(await geo_height(PointInput(easting=E, northing=N)))
    assert out["result"]["height_m"] == 411.1
    assert isinstance(out["result"]["height_m"], float)


@respx.mock
async def test_elevation_profile_maps_comb_altitude(lifespan_started):
    payload = [
        {
            "alts": {"COMB": 411.1, "DTM2": 411.1},
            "dist": 0,
            "easting": 2683531.0,
            "northing": 1247914.0,
        },
        {
            "alts": {"COMB": 455.8, "DTM2": 455.8},
            "dist": 282.8,
            "easting": 2683731.0,
            "northing": 1248114.0,
        },
    ]
    respx.get(f"{API}/profile.json").mock(return_value=httpx.Response(200, json=payload))
    out = json.loads(
        await geo_elevation_profile(
            ProfileInput(
                easting_start=E,
                northing_start=N,
                easting_end=2683731,
                northing_end=1248114,
                nb_points=2,
            )
        )
    )
    assert out["result"][1]["altitude_m"] == 455.8
    assert out["result"][0]["distance_m"] == 0


@respx.mock
async def test_layer_info_lists_fields_and_plain_legend(lifespan_started):
    respx.get(f"{API}/api/MapServer/ch.are.bauzonen").mock(
        return_value=httpx.Response(200, json=_layer_metadata())
    )
    respx.get(f"{API}/all/MapServer/ch.are.bauzonen/legend").mock(
        return_value=httpx.Response(200, html="<div class='legend'><b>Mischzonen</b></div>")
    )
    out = json.loads(await geo_layer_info(LayerInfoInput(layer="ch.are.bauzonen")))
    field_names = [f["name"] for f in out["result"]["fields"]]
    assert "ch_bez_d" in field_names
    assert out["result"]["legend"] == "Mischzonen"  # HTML reduced to text


@respx.mock
async def test_convert_coordinates_parses_string_output(lifespan_started):
    # Reframe returns coordinates as JSON *strings*.
    respx.get(f"{REFRAME}/wgs84tolv95").mock(
        return_value=httpx.Response(200, json={"easting": "2683186.279", "northing": "1247156.732"})
    )
    out = json.loads(
        await geo_convert_coordinates(
            ConvertInput(easting=8.54, northing=47.37, direction="wgs84_to_lv95")
        )
    )
    assert out["result"]["easting"] == pytest.approx(2683186.279)
    assert isinstance(out["result"]["northing"], float)


@respx.mock
async def test_upstream_error_is_sanitised(lifespan_started):
    respx.get(f"{API}/height").mock(
        return_value=httpx.Response(500, text="Internal error stacktrace")
    )
    out = await geo_height(PointInput(easting=E, northing=N))
    assert out.startswith("Error:")
    assert "stacktrace" not in out  # upstream body must not leak to the model


def test_all_nine_tools_registered():
    # Guards against a tool being dropped from the FastMCP registry.
    assert len(mcp._tool_manager.list_tools()) == 9
