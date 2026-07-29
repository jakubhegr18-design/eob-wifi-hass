from __future__ import annotations

from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_DEVICE,
    API_DEVICES_WITH_FCM,
    API_LOGIN,
    BASE_SERVER_URL,
    DOMAIN,
    DEVICE_TYPES_USED_IN_APP,
    LOGGER,
)
from .mqtt_manager import MqttManager

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    mqtt_manager = MqttManager(hass)
    coordinator = EOBWifiCoordinator(hass, entry, mqtt_manager)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: EOBWifiCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.mqtt_manager.shutdown()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True


class EOBWifiCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, mqtt_manager: MqttManager
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]
        self.session = async_get_clientsession(hass)
        self.auth_token: str | None = None
        self.user_id: int | None = None
        self.devices: list[dict] = []
        self.mqtt_manager = mqtt_manager

    async def _login(self) -> None:
        url = f"{BASE_SERVER_URL}{API_LOGIN}"
        async with self.session.post(
            url, json={"userName": self.username, "password": self.password}
        ) as resp:
            if resp.status != 200:
                raise UpdateFailed("Login failed, check credentials")
            data = await resp.json()
            self.auth_token = data.get("authToken")
            self.user_id = data.get("id")

    async def _fetch_devices(self) -> list[dict]:
        if not self.auth_token:
            await self._login()
        url = f"{BASE_SERVER_URL}{API_DEVICES_WITH_FCM}"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        params = {"userId": str(self.user_id)}
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 401:
                await self._login()
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with self.session.get(url, headers=headers, params=params) as r:
                    data = await r.json()
                    return data or []
            elif resp.status != 200:
                raise UpdateFailed(f"Failed to fetch devices: {resp.status}")
            data = await resp.json()
            return data or []

    async def _async_update_data(self) -> dict:
        devices = await self._fetch_devices()
        self.devices = [
            d for d in devices if d.get("deviceType") in DEVICE_TYPES_USED_IN_APP
        ]
        for device in self.devices:
            device_id = device.get("deviceId")
            if self.mqtt_manager.get_client(device_id) is None:
                unique_id = device.get("uniqueIdentifier")
                mqtt_pass = device.get("mqttPass")
                if unique_id and mqtt_pass:
                    await self.mqtt_manager.add_device(device)
        return {"devices": self.devices}

    async def send_command(self, device_data: dict) -> bool:
        if not self.auth_token:
            await self._login()
        url = f"{BASE_SERVER_URL}{API_DEVICE}"
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with self.session.post(url, json=device_data, headers=headers) as resp:
            if resp.status == 401:
                await self._login()
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                async with self.session.post(url, json=device_data, headers=headers) as r:
                    return r.status == 200
            return resp.status == 200
