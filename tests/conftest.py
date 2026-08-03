"""Shared fixtures for ChargeWindow tests."""

from __future__ import annotations

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(request: pytest.FixtureRequest) -> None:
    """Enable custom integrations for every test."""
    try:
        request.getfixturevalue("enable_custom_integrations")
    except pytest.FixtureLookupError:
        # Allows the pure response-model tests to run on Windows with plugin
        # auto-loading disabled; the full suite runs with the fixture on Linux CI.
        pass
