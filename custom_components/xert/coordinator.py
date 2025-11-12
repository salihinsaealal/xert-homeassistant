"""Data update coordinator for Xert integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    API_BASE_URL,
    TOKEN_URL,
    ENDPOINT_TRAINING_INFO,
    ENDPOINT_WORKOUTS,
    ENDPOINT_ACTIVITY_LIST,
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_EXPIRES_IN,
    CONF_TOKEN_EXPIRES_AT,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
)

_LOGGER = logging.getLogger(__name__)


class XertDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Xert data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        config_entry: ConfigEntry,
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.session = session
        self.config_entry = config_entry
        self.config_data = config_entry.data
        self._access_token = config_entry.data.get(CONF_ACCESS_TOKEN)
        self._refresh_token = config_entry.data.get(CONF_REFRESH_TOKEN)
        self._token_expires = None
        self._refresh_lock = asyncio.Lock()
        self._is_refreshing = False
        
        # Load token expiry from stored timestamp or calculate from expires_in
        if config_entry.data.get(CONF_TOKEN_EXPIRES_AT):
            self._token_expires = dt_util.parse_datetime(
                config_entry.data[CONF_TOKEN_EXPIRES_AT]
            )
        elif config_entry.data.get(CONF_EXPIRES_IN):
            self._token_expires = dt_util.utcnow() + timedelta(
                seconds=config_entry.data[CONF_EXPIRES_IN]
            )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoints."""
        try:
            # Check if token needs refresh
            await self._ensure_valid_token()

            # Fetch all data concurrently for efficiency
            tasks = [
                self._fetch_training_info(),
                self._fetch_workouts(),
                self._fetch_recent_activities(),
            ]

            training_info, workouts, activities = await asyncio.gather(*tasks)

            # Organize data into entity structure
            return {
                "fitness_status": self._process_fitness_status(training_info),
                "training_progress": self._process_training_progress(training_info, activities),
                "workout_manager": self._process_workout_manager(workouts),
                "recent_activity": self._process_recent_activity(activities),
                "token_status": self._process_token_status(),
                "wotd": self._process_wotd(training_info),
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Xert API: {err}") from err

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        if not self._token_expires:
            _LOGGER.warning("Token expiry time not set, attempting refresh")
            await self._refresh_access_token()
            return
        
        # Refresh proactively 1 hour before expiry to avoid edge cases
        refresh_threshold = self._token_expires - timedelta(hours=1)
        
        if dt_util.utcnow() >= refresh_threshold:
            await self._refresh_access_token()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token with proper locking and persistence."""
        if not self._refresh_token:
            raise ConfigEntryAuthFailed("No refresh token available")

        # Use lock to prevent concurrent refresh attempts
        async with self._refresh_lock:
            # Check if another task already refreshed while we were waiting
            if self._is_refreshing:
                return
            
            self._is_refreshing = True
            
            try:
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                }

                _LOGGER.debug("Attempting to refresh access token")
                
                async with self.session.post(
                    TOKEN_URL,
                    data=data,
                    auth=aiohttp.BasicAuth(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 400:
                        _LOGGER.error("Token refresh failed with 400: %s", response_text)
                        raise ConfigEntryAuthFailed(
                            "Token refresh failed: Invalid or expired refresh token. "
                            "Please re-authenticate."
                        )
                    
                    if response.status == 401:
                        _LOGGER.error("Token refresh failed with 401: %s", response_text)
                        raise ConfigEntryAuthFailed(
                            "Token refresh failed: Unauthorized. Please re-authenticate."
                        )
                    
                    if response.status != 200:
                        _LOGGER.error(
                            "Token refresh failed with status %s: %s",
                            response.status,
                            response_text,
                        )
                        raise UpdateFailed(
                            f"Token refresh failed with status {response.status}"
                        )

                    token_data = await response.json()
                    
                    # Update tokens in memory
                    self._access_token = token_data["access_token"]
                    self._refresh_token = token_data.get(
                        "refresh_token", self._refresh_token
                    )
                    self._token_expires = dt_util.utcnow() + timedelta(
                        seconds=token_data["expires_in"]
                    )
                    
                    _LOGGER.info(
                        "Successfully refreshed access token, expires at %s",
                        self._token_expires.isoformat(),
                    )
                    
                    # Persist tokens to config entry
                    await self._persist_tokens()

            except ConfigEntryAuthFailed:
                # Re-raise auth errors to trigger reauth flow
                raise
            except aiohttp.ClientError as err:
                _LOGGER.error("Network error during token refresh: %s", err)
                raise UpdateFailed(f"Network error during token refresh: {err}") from err
            except Exception as err:
                _LOGGER.error("Unexpected error during token refresh: %s", err)
                raise UpdateFailed(f"Token refresh error: {err}") from err
            finally:
                self._is_refreshing = False

    async def _persist_tokens(self) -> None:
        """Persist updated tokens to config entry."""
        try:
            # Get the config entry
            entry = self.config_entry
            
            # Update config entry with new tokens
            new_data = {
                **entry.data,
                CONF_ACCESS_TOKEN: self._access_token,
                CONF_REFRESH_TOKEN: self._refresh_token,
                CONF_TOKEN_EXPIRES_AT: self._token_expires.isoformat()
                if self._token_expires
                else None,
            }
            
            self.hass.config_entries.async_update_entry(entry, data=new_data)
            _LOGGER.debug("Persisted updated tokens to config entry")
            
        except Exception as err:
            _LOGGER.error("Failed to persist tokens: %s", err)

    async def _make_api_request(self, endpoint: str, params: dict = None) -> dict:
        """Make an authenticated API request."""
        headers = {"Authorization": f"Bearer {self._access_token}"}
        url = f"{API_BASE_URL}/{endpoint}"

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 401:
                    # Token might be expired, try to refresh
                    await self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self.session.get(url, headers=headers, params=params) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()
                else:
                    response.raise_for_status()
                    return await response.json()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"API request failed: {err}") from err

    async def _fetch_training_info(self) -> dict:
        """Fetch training and fitness information."""
        return await self._make_api_request(ENDPOINT_TRAINING_INFO)

    async def _fetch_workouts(self) -> dict:
        """Fetch available workouts."""
        return await self._make_api_request(ENDPOINT_WORKOUTS)

    async def _fetch_recent_activities(self) -> dict:
        """Fetch recent activities."""
        # Get activities from last 30 days
        to_date = dt_util.utcnow()
        from_date = to_date - timedelta(days=30)
        params = {
            "from": int(from_date.timestamp()),
            "to": int(to_date.timestamp()),
        }
        return await self._make_api_request(ENDPOINT_ACTIVITY_LIST, params)

    def _process_fitness_status(self, training_info: dict) -> dict:
        """Process fitness status data based on actual API response."""
        if not training_info.get("success"):
            return {"state": "Unknown", "attributes": {}}

        # Only keep status as state, and minimal unique attributes if available
        return {
            "state": training_info.get("status", "Unknown"),
            "attributes": {},
        }

    def _process_training_progress(self, training_info: dict, activities: dict) -> dict:
        """Process training progress data."""
        if not training_info.get("success"):
            return {"state": 0, "attributes": {}}

        signature = training_info.get("signature", {})
        tl = training_info.get("tl", {})
        target_xss = training_info.get("targetXSS", {})
        attrs = {
            "weight": training_info.get("weight"),
            "signature_ftp": signature.get("ftp"),
            "signature_ltp": signature.get("ltp"),
            "signature_hie": signature.get("hie"),
            "signature_pp": signature.get("pp"),
            "tl_low": tl.get("low"),
            "tl_high": tl.get("high"),
            "tl_peak": tl.get("peak"),
            "tl_total": tl.get("total"),
            "target_xss_low": target_xss.get("low"),
            "target_xss_high": target_xss.get("high"),
            "target_xss_peak": target_xss.get("peak"),
            "target_xss_total": target_xss.get("total"),
            "source": training_info.get("source"),
            "success": training_info.get("success"),
        }
        return {
            "state": 0,
            "attributes": attrs,
        }

    def _process_workout_manager(self, workouts: dict) -> dict:
        """Process workout manager data."""
        if not workouts.get("success"):
            return {"state": 0, "attributes": {}}

        workout_list = workouts.get("workouts", [])
        return {
            "state": len(workout_list),
            "attributes": {
                "total_workouts": len(workout_list),
                "last_modified": self._get_last_workout_date(workout_list),
                "sample_workouts": [w.get("name") for w in workout_list[:3]],
            },
        }

    def _process_recent_activity(self, activities: dict) -> dict:
        """Process recent activity data."""
        if not activities.get("success"):
            return {"state": "No recent activity", "attributes": {}}

        activity_list = activities.get("activities", [])
        recent = activity_list[0] if activity_list else {}
        start_date = recent.get("start_date", {})

        return {
            "state": recent.get("name", "No recent activity"),
            "attributes": {
                "activity_type": recent.get("activity_type"),
                # Flattened start date attributes
                "activity_date": start_date.get("date"),
                "activity_timezone": start_date.get("timezone"),
                "activity_timestamp": start_date.get("timestamp"),
                "description": recent.get("description"),
                "path": recent.get("path"),
            },
        }

    def _process_token_status(self) -> dict:
        """Process token status data."""
        status = "Valid"
        if not self._access_token:
            status = "Invalid"
        elif self._token_expires and dt_util.utcnow() >= self._token_expires:
            status = "Expired"

        return {
            "state": status,
            "attributes": {
                "token_expiry": self._token_expires.isoformat() if self._token_expires else None,
                "refresh_token_available": bool(self._refresh_token),
                "last_successful_call": dt_util.utcnow().isoformat(),
            },
        }

    def _get_last_activity_date(self, activities: dict) -> str | None:
        """Get the date of the most recent activity."""
        activity_list = activities.get("activities", [])
        if activity_list:
            start_date = activity_list[0].get("start_date", {})
            return start_date.get("date")
        return None

    def _get_last_workout_date(self, workouts: list) -> str | None:
        """Get the date of the last modified workout."""
        if workouts:
            # Convert timestamp to date string
            timestamp = workouts[0].get("last_modified")
            if timestamp:
                return datetime.fromtimestamp(timestamp).isoformat()
        return None

    def _process_wotd(self, training_info: dict) -> dict:
        """Process Workout of the Day (WOTD) data."""
        wotd = training_info.get("wotd", {})
        if not wotd:
            return {"state": None, "attributes": {}}
        return {
            "state": wotd.get("name"),
            "attributes": {
                "type": wotd.get("type"),
                "description": wotd.get("description"),
                "workout_id": wotd.get("workoutId"),
                "url": wotd.get("url"),
                "difficulty": wotd.get("difficulty"),
            },
        }

    async def download_workout(self, workout_id: str, format_type: str = "zwo") -> bytes:
        """Download a workout file in specified format."""
        url = f"https://www.xertonline.com/oauth/workout-download/{workout_id}.{format_type}"
        headers = {"Authorization": f"Bearer {self._access_token}"}
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 401:
                    # Token expired, refresh and retry
                    await self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self.session.get(url, headers=headers) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.read()
                else:
                    response.raise_for_status()
                    return await response.read()
        except Exception as err:
            _LOGGER.error("Failed to download workout %s: %s", workout_id, err)
            raise