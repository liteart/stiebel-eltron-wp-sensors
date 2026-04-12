"""HTTP client for the Stiebel Eltron ISG web interface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import HEAT_PUMP_URL_PATH, PLANT_URL_PATH
from .scraper import (
    IntegrationSnapshot,
    is_heat_pump_page,
    is_login_page,
    is_plant_page,
    merge_snapshots,
    parse_heat_pump_page,
    parse_plant_page,
)


class StiebelEltronIsgError(Exception):
    """Base exception for ISG access failures."""


class StiebelEltronIsgCannotConnectError(StiebelEltronIsgError):
    """Raised when the ISG cannot be reached."""


class StiebelEltronIsgAuthRequiredError(StiebelEltronIsgError):
    """Raised when the ISG requires authentication."""


class StiebelEltronIsgInvalidAuthError(StiebelEltronIsgError):
    """Raised when ISG credentials are invalid."""


class StiebelEltronIsgParseError(StiebelEltronIsgError):
    """Raised when the returned page cannot be parsed."""


@dataclass(slots=True, frozen=True)
class StiebelEltronIsgProbeResult:
    """Result of probing the ISG landing page."""

    login_required: bool
    snapshot: IntegrationSnapshot | None


class StiebelEltronIsgClient:
    """Small client for the ISG heat pump page."""

    def __init__(
        self,
        *,
        session: ClientSession,
        host: str,
        username: str = "",
        password: str = "",
        timeout: float = 15.0,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._host = host.strip().rstrip("/")
        self._username = username
        self._password = password
        self._timeout = timeout

    @property
    def host(self) -> str:
        """Return the configured host."""
        return self._host

    @property
    def status_url(self) -> str:
        """Return the fixed heat pump status URL."""
        return f"http://{self._host}{HEAT_PUMP_URL_PATH}"

    @property
    def plant_url(self) -> str:
        """Return the fixed plant status URL."""
        return f"http://{self._host}{PLANT_URL_PATH}"

    async def async_probe(self) -> StiebelEltronIsgProbeResult:
        """Probe whether the target page needs authentication."""
        page = await self._async_request("GET", self.status_url)
        if is_heat_pump_page(page):
            return StiebelEltronIsgProbeResult(
                login_required=False,
                snapshot=parse_heat_pump_page(page),
            )
        if is_login_page(page):
            return StiebelEltronIsgProbeResult(login_required=True, snapshot=None)
        raise StiebelEltronIsgParseError("Unexpected ISG landing page")

    async def async_get_snapshot(self) -> IntegrationSnapshot:
        """Fetch the live heat pump snapshot."""
        heat_pump_page = await self._async_fetch_page(
            self.status_url,
            is_heat_pump_page,
        )
        return await self._async_build_snapshot(heat_pump_page)

    async def _async_build_snapshot(self, heat_pump_page: str) -> IntegrationSnapshot:
        """Build a combined snapshot from all required ISG pages."""
        try:
            heat_pump_snapshot = parse_heat_pump_page(heat_pump_page)
            plant_page = await self._async_fetch_page(self.plant_url, is_plant_page)
            plant_snapshot = parse_plant_page(plant_page)
        except ValueError as err:
            raise StiebelEltronIsgParseError(str(err)) from err
        return merge_snapshots(heat_pump_snapshot, plant_snapshot)

    async def _async_fetch_page(
        self,
        url: str,
        success_predicate: Callable[[str], bool],
    ) -> str:
        """Fetch a page, authenticating against that page if required."""
        page = await self._async_request("GET", url)
        if success_predicate(page):
            return page

        if not is_login_page(page):
            raise StiebelEltronIsgParseError("Unexpected ISG page")

        if not self._username or not self._password:
            raise StiebelEltronIsgAuthRequiredError("Credentials required")

        page = await self._async_request(
            "POST",
            url,
            data={
                "make": "send",
                "user": self._username,
                "pass": self._password,
            },
        )
        if success_predicate(page):
            return page
        if is_login_page(page):
            if "Login fehlgeschlagen" in page:
                raise StiebelEltronIsgInvalidAuthError("Invalid credentials")
            raise StiebelEltronIsgAuthRequiredError("Credentials required")
        raise StiebelEltronIsgParseError("Unexpected response after login")

    async def _async_request(self, method: str, url: str, **kwargs) -> str:
        """Perform a request against the ISG."""
        try:
            async with self._session.request(
                method,
                url,
                timeout=ClientTimeout(total=self._timeout),
                **kwargs,
            ) as response:
                response.raise_for_status()
                return await response.text()
        except ClientError as err:
            raise StiebelEltronIsgCannotConnectError(str(err)) from err
