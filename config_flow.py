"""Config flow for Xert integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    TOKEN_URL,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_EXPIRES_IN,
)

_LOGGER = logging.getLogger(__name__)


class XertConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xert."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Attempt to authenticate with Xert
                token_data = await self._authenticate(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )

                # Check if we already have an entry
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

                # Create the config entry
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_ACCESS_TOKEN: token_data["access_token"],
                        CONF_REFRESH_TOKEN: token_data["refresh_token"],
                        CONF_EXPIRES_IN: token_data["expires_in"],
                    },
                )

            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Authentication error: %s", err)
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def _authenticate(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate with Xert API."""
        data = {
            "grant_type": "password",
            "username": username,
            "password": password,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                TOKEN_URL,
                data=data,
                auth=aiohttp.BasicAuth(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
            ) as response:
                if response.status != 200:
                    raise Exception(f"Authentication failed: {response.status}")

                return await response.json() 