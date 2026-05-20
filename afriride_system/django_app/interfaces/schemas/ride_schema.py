"""Minimal JSON schema for ride creation requests."""

RIDE_REQUEST_SCHEMA = {
    "type": "object",
    "required": ["rider_id", "origin", "destination"],
    "properties": {
        "rider_id": {"type": "string", "format": "uuid"},
        "origin": {"type": "object"},
        "destination": {"type": "object"},
    },
}
