"""Constants for the ChargeWindow integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "chargewindow"

# Config entry keys
CONF_BASE_URL: Final = "base_url"
CONF_AREA: Final = "area"
CONF_CURRENCY: Final = "currency"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_BASE_URL: Final = "https://chargewindow.eu"
DEFAULT_AREA: Final = "DK2"
DEFAULT_CURRENCY: Final = "DKK"
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 5
MIN_SCAN_INTERVAL_MINUTES: Final = 1
MAX_SCAN_INTERVAL_MINUTES: Final = 60

# Supported bidding zones / areas
SUPPORTED_AREAS: Final = [
    "DK1",
    "DK2",
    "SE1",
    "SE2",
    "SE3",
    "SE4",
    "NO1",
    "NO2",
    "NO3",
    "NO4",
    "NO5",
]

# API
API_PATH: Final = "/api/integrations/homeassistant/state"
REQUEST_TIMEOUT: Final = 20
