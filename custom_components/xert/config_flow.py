"""Config flow for Xert integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    TOKEN_URL,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_EXPIRES_IN,
    CONF_TOKEN_EXPIRES_AT,
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

                # Calculate token expiry timestamp
                token_expires_at = dt_util.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                )
                
                # Create the config entry
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_ACCESS_TOKEN: token_data["access_token"],
                        CONF_REFRESH_TOKEN: token_data["refresh_token"],
                        CONF_EXPIRES_IN: token_data["expires_in"],
                        CONF_TOKEN_EXPIRES_AT: token_expires_at.isoformat(),
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

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Handle reauth flow when token refresh fails."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth confirmation step."""
        errors = {}

        if user_input is not None:
            try:
                # Get username from existing entry
                username = self._reauth_entry.data[CONF_USERNAME]
                
                # Attempt to authenticate with new password
                token_data = await self._authenticate(
                    username, user_input[CONF_PASSWORD]
                )

                # Calculate token expiry timestamp
                token_expires_at = dt_util.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                )

                # Update the existing config entry with new tokens
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        CONF_USERNAME: username,
                        CONF_ACCESS_TOKEN: token_data["access_token"],
                        CONF_REFRESH_TOKEN: token_data["refresh_token"],
                        CONF_EXPIRES_IN: token_data["expires_in"],
                        CONF_TOKEN_EXPIRES_AT: token_expires_at.isoformat(),
                    },
                )

                # Reload the config entry to apply new tokens
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)

                return self.async_abort(reason="reauth_successful")

            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error during reauth: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error("Authentication error during reauth: %s", err)
                errors["base"] = "invalid_auth"

        # Show reauth form
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={
                "username": self._reauth_entry.data[CONF_USERNAME],
            },
            errors=errors,
        ) 