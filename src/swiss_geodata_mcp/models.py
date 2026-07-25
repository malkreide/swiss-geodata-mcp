"""Pydantic v2 response envelopes.

Every tool wraps its payload in a :class:`GeoEnvelope` so the model always sees
the upstream ``source`` and the ``provenance`` of the data. This server uses
Architecture A (live-API-only), so ``provenance`` is always ``live_api`` — there
is no local cache or dump layer.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

PROVENANCE_LIVE = "live_api"


class GeoEnvelope(BaseModel):
    """Uniform envelope returned (as JSON) by every tool."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(description="Upstream geo.admin.ch service the data came from.")
    provenance: str = Field(
        default=PROVENANCE_LIVE,
        description="Always 'live_api' — this server queries upstream on every call.",
    )
    query: dict[str, Any] | None = Field(
        default=None, description="Echo of the resolved query parameters."
    )
    result: Any = Field(default=None, description="The tool payload.")
    note: str | None = Field(
        default=None, description="Optional caveat or legal note for the caller."
    )

    def to_json(self) -> str:
        return self.model_dump_json(indent=2, exclude_none=True)
