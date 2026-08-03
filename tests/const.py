"""Test data for ChargeWindow."""

from __future__ import annotations

BASE_URL = "https://chargewindow.test"
API_URL = f"{BASE_URL}/api/integrations/homeassistant/state"

STATE_PAYLOAD = {
    "area": "DK2",
    "currency": "DKK",
    "requestedCurrency": "EUR",
    "generatedAtUtc": "2026-08-04T08:00:00Z",
    "currentPrice": {"allInDkkPerKWh": 1.25, "spotOnly": 0.55},
    "isCheapNow": False,
    "isNextHourInCheapestWindow": True,
    "cheapestWindow": {
        "startLocal": "2026-08-04T12:00:00",
        "endLocal": "2026-08-04T15:00:00",
        "avgPrice": 0.75,
    },
    "savingsVsChargingNow": {"absolute": 1.5, "percent": 40.0},
    "co2IntensityNow": 29.0,
    "hours": [
        {
            "hourLocal": "2026-08-04T11:00:00",
            "priceAllIn": -0.15,
            "isPast": True,
            "isCheap": False,
        },
        {
            "hourLocal": "2026-08-04T12:00:00",
            "priceAllIn": 0.75,
            "isPast": False,
            "isCheap": True,
        },
    ],
}
