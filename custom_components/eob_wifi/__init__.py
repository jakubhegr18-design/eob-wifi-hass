from __future__ import annotations

from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_DEVICES_WITH_FCM,
    API_LOGIN,
    BASE_SERVER_URL,
    DOMAIN,
    DEVICE_TYPES_USED_IN_APP,
    LOGGER,
)
from .mqtt_manager import MqttManager

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH]

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
            dtype = device.get("deviceType")
            variant = device.get("deviceVariant")

            self._merge_mqtt_state(device)

            therm_data = device.get("thermData") or {}
            therm_settings = device.get("thermSettings") or {}
            device_data = device.get("deviceData") or {}
            temp = therm_data if isinstance(therm_data, dict) and therm_data else therm_settings
            LOGGER.debug(
                "device %s: type=%s variant=%s isAnalogMode=%s isAuto=%s isSwitchedOn=%s "
                "actualTemp=%s desiredTemp=%s tempSource=%s thermData=%s thermSettings=%s",
                device.get("name"), dtype, variant,
                therm_data.get("isAnalogMode") if isinstance(therm_data, dict) else None,
                therm_settings.get("isAuto") if isinstance(therm_settings, dict) else None,
                device_data.get("isSwitchedOn") if isinstance(device_data, dict) else None,
                temp.get("actualTemp"),
                temp.get("desiredTemp"),
                "thermData" if isinstance(therm_data, dict) and therm_data else "thermSettings",
                dict(therm_data) if isinstance(therm_data, dict) else therm_data,
                dict(therm_settings) if isinstance(therm_settings, dict) else therm_settings,
            )
            if self.mqtt_manager.get_client(device_id) is None:
                unique_id = device.get("uniqueIdentifier")
                mqtt_pass = device.get("mqttPass")
                if unique_id and mqtt_pass:
                    await self.mqtt_manager.add_device(device)
        return {"devices": self.devices}

    def _merge_mqtt_state(self, device: dict) -> None:
        """Merge MQTT push state into device dict when REST API returns no data."""
        device_id = device.get("deviceId")
        mqtt_state = self.mqtt_manager.get_state(device_id)
        if not mqtt_state:
            return

        device.setdefault("mqttState", {})
        for k, v in mqtt_state.items():
            device["mqttState"][f"0x{k:04X}"] = v.hex()

        LOGGER.debug("MQTT state for device %s: %s", device.get("name"), device["mqttState"])

        key_01 = (0x30 << 8) | 0x01
        payload = mqtt_state.get(key_01)
        if payload and len(payload) >= 1:
            device.setdefault("deviceData", {})["isSwitchedOn"] = bool(payload[0])

        key_02 = (0x30 << 8) | 0x02
        payload = mqtt_state.get(key_02)
        if payload and len(payload) >= 1:
            device.setdefault("thermSettings", {})["isAuto"] = payload[0] == 1

        key_0b = (0x30 << 8) | 0x0B
        payload = mqtt_state.get(key_0b)
        if payload and len(payload) >= 2:
            actual_raw = payload[0]
            desired_raw = payload[1]
            device.setdefault("thermData", {})
            device["thermData"]["actualTemp"] = actual_raw / 2.0
            device["thermData"]["desiredTemp"] = desired_raw / 2.0
            LOGGER.debug(
                "MQTT→thermData for %s: actualTemp=%.1f (0x%02X) desiredTemp=%.1f (0x%02X) "
                "raw=%s — PLEASE VERIFY field mapping against app!",
                device.get("name"),
                device["thermData"]["actualTemp"], actual_raw,
                device["thermData"]["desiredTemp"], desired_raw,
                payload.hex()
            )


