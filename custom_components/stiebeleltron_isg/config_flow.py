"""Config flow for the Stiebel Eltron ISG integration."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig

from .client import (
    StiebelEltronIsgAuthRequiredError,
    StiebelEltronIsgCannotConnectError,
    StiebelEltronIsgClient,
    StiebelEltronIsgInvalidAuthError,
    StiebelEltronIsgParseError,
)
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_TIMEOUT,
    DOMAIN,
    NAME,
)


def _validate_host(host: str) -> str:
    """Validate a configured host value."""
    candidate = host.strip()
    if not candidate:
        raise vol.Invalid("host")

    try:
        ip_address(candidate)
    except ValueError:
        candidate = cv.string(candidate)

    return candidate


async def _async_validate_input(hass, user_input: dict[str, Any]) -> str:
    """Validate the user input against the configured ISG."""
    host = _validate_host(user_input[CONF_HOST])
    client = StiebelEltronIsgClient(
        session=async_get_clientsession(hass),
        host=host,
        username=user_input.get(CONF_USERNAME, "").strip(),
        password=user_input.get(CONF_PASSWORD, ""),
        timeout=float(user_input[CONF_TIMEOUT]),
    )

    result = await client.async_probe()
    if (
        result.login_required
        and not user_input.get(CONF_USERNAME)
        and not user_input.get(CONF_PASSWORD)
    ):
        raise StiebelEltronIsgAuthRequiredError
    if result.login_required:
        await client.async_get_snapshot()

    return host


class StiebelEltronIsgConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Stiebel Eltron ISG."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return StiebelEltronIsgOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                host = await _async_validate_input(self.hass, user_input)
            except vol.Invalid:
                errors["base"] = "invalid_host"
            except StiebelEltronIsgCannotConnectError:
                errors["base"] = "cannot_connect"
            except StiebelEltronIsgInvalidAuthError:
                errors["base"] = "invalid_auth"
            except StiebelEltronIsgAuthRequiredError:
                errors["base"] = "credentials_required"
            except StiebelEltronIsgParseError:
                errors["base"] = "cannot_parse"
            else:
                await self.async_set_unique_id(host.lower())
                self._abort_if_unique_id_configured()

                data = {
                    CONF_HOST: host,
                    CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
                    CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                }
                options = {
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_TIMEOUT: float(user_input[CONF_TIMEOUT]),
                }
                return self.async_create_entry(title=f"{NAME} ({host})", data=data, options=options)

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                host = await _async_validate_input(self.hass, user_input)
            except vol.Invalid:
                errors = {"base": "invalid_host"}
            except StiebelEltronIsgCannotConnectError:
                errors = {"base": "cannot_connect"}
            except StiebelEltronIsgInvalidAuthError:
                errors = {"base": "invalid_auth"}
            except StiebelEltronIsgAuthRequiredError:
                errors = {"base": "credentials_required"}
            except StiebelEltronIsgParseError:
                errors = {"base": "cannot_parse"}
            else:
                await self.async_set_unique_id(host.lower())
                self._abort_if_unique_id_mismatch(reason="different_host")
                self.hass.config_entries.async_update_entry(
                    entry,
                    title=f"{NAME} ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
                    },
                    options={
                        **entry.options,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_TIMEOUT: float(user_input[CONF_TIMEOUT]),
                    },
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")

        defaults = {
            CONF_HOST: entry.data[CONF_HOST],
            CONF_USERNAME: entry.data.get(CONF_USERNAME, ""),
            CONF_PASSWORD: entry.data.get(CONF_PASSWORD, ""),
            CONF_SCAN_INTERVAL: entry.options.get(
                CONF_SCAN_INTERVAL,
                DEFAULT_SCAN_INTERVAL_MINUTES,
            ),
            CONF_TIMEOUT: entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(defaults),
            errors=errors,
        )

    def _build_schema(self, user_input: dict[str, Any] | None = None) -> vol.Schema:
        """Build the config flow schema."""
        data = user_input or {}
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
                vol.Optional(CONF_USERNAME, default=data.get(CONF_USERNAME, "")): str,
                vol.Optional(CONF_PASSWORD, default=data.get(CONF_PASSWORD, "")): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=data.get(
                        CONF_SCAN_INTERVAL,
                        DEFAULT_SCAN_INTERVAL_MINUTES,
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        mode="box",
                    )
                ),
                vol.Optional(
                    CONF_TIMEOUT,
                    default=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=60,
                        mode="box",
                    )
                ),
            }
        )


class StiebelEltronIsgOptionsFlow(config_entries.OptionsFlow):
    """Handle Stiebel Eltron ISG options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    CONF_TIMEOUT: float(user_input[CONF_TIMEOUT]),
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            DEFAULT_SCAN_INTERVAL_MINUTES,
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=60,
                            mode="box",
                        )
                    ),
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=5,
                            max=60,
                            mode="box",
                        )
                    ),
                }
            ),
            errors={},
        )
