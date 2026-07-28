"""Constants for the Domee integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "domee"
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"

DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)
