"""Dual-transport entry point.

``stdio`` by default (Claude Desktop); set ``SWISS_GEODATA_TRANSPORT`` to
``streamable-http`` or ``sse`` for cloud deployments, with ``HOST`` / ``PORT``
controlling the HTTP binding (read by the FastMCP instance in server.py).
"""

import logging
import os

from swiss_geodata_mcp.server import mcp

logger = logging.getLogger("swiss_geodata_mcp")

_VALID_TRANSPORTS = {"stdio", "streamable-http", "sse"}


def main() -> None:
    transport = os.getenv("SWISS_GEODATA_TRANSPORT", "stdio").strip().lower()
    if transport not in _VALID_TRANSPORTS:
        logger.warning("Unknown transport %r — falling back to stdio.", transport)
        transport = "stdio"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
