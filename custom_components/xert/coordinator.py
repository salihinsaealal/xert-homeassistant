"""Data update coordinator for Xert integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
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
        config_data: dict[str, Any],
        update_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.session = session
        self.config_data = config_data
        self._access_token = config_data.get(CONF_ACCESS_TOKEN)
        self._refresh_token = config_data.get(CONF_REFRESH_TOKEN)
        self._token_expires = None
        if config_data.get(CONF_EXPIRES_IN):
            self._token_expires = dt_util.utcnow() + timedelta(
                seconds=config_data[CONF_EXPIRES_IN]
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
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with Xert API: {err}") from err

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid access token."""
        if self._token_expires and dt_util.utcnow() >= self._token_expires:
            await self._refresh_access_token()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token."""
        if not self._refresh_token:
            raise UpdateFailed("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        try:
            async with self.session.post(
                TOKEN_URL,
                data=data,
                auth=aiohttp.BasicAuth(OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Token refresh failed: {response.status}")

                token_data = await response.json()
                self._access_token = token_data["access_token"]
                self._refresh_token = token_data.get("refresh_token", self._refresh_token)
                self._token_expires = dt_util.utcnow() + timedelta(
                    seconds=token_data["expires_in"]
                )

        except Exception as err:
            raise UpdateFailed(f"Token refresh error: {err}") from err

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

        signature = training_info.get("signature", {})
        tl = training_info.get("tl", {})
        
        return {
            "state": training_info.get("status", "Unknown"),
            "attributes": {
                "ftp": signature.get("ftp"),
                "ltp": signature.get("ltp"),
                "hie": signature.get("hie"),
                "pp": signature.get("pp"),
                "weight": training_info.get("weight"),
                "training_load_low": tl.get("low"),
                "training_load_high": tl.get("high"),
                "training_load_peak": tl.get("peak"),
                "training_load_total": tl.get("total"),
                "target_xss": training_info.get("targetXSS", {}),
                "source": training_info.get("source"),
            },
        }

    def _process_training_progress(self, training_info: dict, activities: dict) -> dict:
        """Process training progress data."""
        if not training_info.get("success"):
            return {"state": 0, "attributes": {}}

        wotd = training_info.get("wotd", {})
        
        return {
            "state": wotd.get("difficulty", 0),
            "attributes": {
                "workout_of_the_day": wotd.get("name"),
                "workout_type": wotd.get("type"),
                "workout_description": wotd.get("description"),
                "workout_id": wotd.get("workoutId"),
                "workout_url": wotd.get("url"),
                "last_activity_date": self._get_last_activity_date(activities),
            },
        }

    def _process_workout_manager(self, workouts: dict) -> dict:
        """Process workout manager data."""
        if not workouts.get("success"):
            return {"state": 0, "attributes": {}}

        workout_list = workouts.get("workouts", [])
        recommended = workout_list[0] if workout_list else {}
        
        return {
            "state": len(workout_list),
            "attributes": {
                "total_workouts": len(workout_list),
                "workout_names": [w.get("name") for w in workout_list],
                "recommended_workout": recommended.get("name"),
                "workout_description": recommended.get("description"),
                "last_modified": self._get_last_workout_date(workout_list),
            },
        }

    def _process_recent_activity(self, activities: dict) -> dict:
        """Process recent activity data."""
        if not activities.get("success"):
            return {"state": "No recent activity", "attributes": {}}

        activity_list = activities.get("activities", [])
        recent = activity_list[0] if activity_list else {}

        return {
            "state": recent.get("name", "No recent activity"),
            "attributes": {
                "activity_type": recent.get("activity_type"),
                "start_date": recent.get("start_date", {}).get("date"),
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