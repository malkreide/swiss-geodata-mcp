"""Live integration tests against the real geo.admin.ch API.

Excluded from PR/push CI (they depend on api3.geo.admin.ch availability); run
nightly or on demand with ``pytest tests/ -m live``. Anchor point: the school
building at Seilergraben 76, Zürich (LV95 2683531 / 1247914).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from swiss_geodata_mcp.server import (
    ConvertInput,
    IdentifyInput,
    PointInput,
    SearchLayersInput,
    _lifespan,
    geo_convert_coordinates,
    geo_height,
    geo_identify,
    geo_municipality_at,
    geo_search_layers,
    geo_zoning_at,
    mcp,
)

pytestmark = pytest.mark.live

E, N = 2683531, 1247914


@pytest.fixture
async def lifespan_started():
    async with _lifespan(mcp):
        yield


async def test_live_search_layers(lifespan_started):
    out = json.loads(await geo_search_layers(SearchLayersInput(query="bauzonen")))
    assert any(r["layer_id"] == "ch.are.bauzonen" for r in out["result"])


async def test_live_zoning_at_anchor(lifespan_started):
    out = json.loads(await geo_zoning_at(PointInput(easting=E, northing=N)))
    assert out["result"], "expected a building zone at the anchor point"
    assert out["result"][0]["canton"] == "ZH"


async def test_live_municipality_at_anchor(lifespan_started):
    out = json.loads(await geo_municipality_at(PointInput(easting=E, northing=N)))
    assert out["result"]["municipality"] == "Zürich"
    assert str(out["result"]["bfs_number"]) == "261"


async def test_live_height_at_anchor(lifespan_started):
    out = json.loads(await geo_height(PointInput(easting=E, northing=N)))
    assert 400 < out["result"]["height_m"] < 420


async def test_live_convert_roundtrip(lifespan_started):
    out = json.loads(
        await geo_convert_coordinates(
            ConvertInput(easting=8.54, northing=47.37, direction="wgs84_to_lv95")
        )
    )
    assert 2_450_000 < out["result"]["easting"] < 2_850_000


async def test_live_identify_soft_miss_is_not_error(lifespan_started):
    # A point in Lake Zurich has no building zone — soft miss, HTTP 200.
    out = json.loads(
        await geo_identify(
            IdentifyInput(layer="ch.are.bauzonen", easting=2_690_000, northing=1_230_000)
        )
    )
    assert "provenance" in out  # a valid envelope, not an error string
