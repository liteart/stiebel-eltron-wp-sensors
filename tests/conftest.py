"""Pytest fixtures for the Stiebel Eltron ISG integration."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_PATH = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test."""
    yield


@pytest.fixture
def login_page() -> str:
    """Return the sample login page."""
    return (FIXTURES_PATH / "login_page.html").read_text(encoding="utf-8")


@pytest.fixture
def login_failed_page() -> str:
    """Return the sample failed-login page."""
    return (FIXTURES_PATH / "login_failed_page.html").read_text(encoding="utf-8")


@pytest.fixture
def heat_pump_page() -> str:
    """Return the sample heat pump details page."""
    return (FIXTURES_PATH / "heat_pump_page.html").read_text(encoding="utf-8")


@pytest.fixture
def anlage_page() -> str:
    """Return the sample plant details page."""
    return (FIXTURES_PATH / "anlage_page.html").read_text(encoding="utf-8")


@pytest.fixture
def no_auth_host() -> str:
    """Return a fake host for unauthenticated access."""
    return "isg-no-auth.local"


@pytest.fixture
def auth_host() -> str:
    """Return a fake host for authenticated access."""
    return "isg-auth.local"
