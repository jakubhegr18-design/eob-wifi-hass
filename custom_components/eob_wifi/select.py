"""Select entities for EOB WiFi devices - TS11 Therm timezone."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import (
    DEVICE_TYPE_NAMES,
    DEVICE_TYPE_THERMOSTATS,
    DOMAIN,
    MANUFACTURER,
    TIMEZONE_OPTIONS,
    _is_analog_mode,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EOBWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices:
        dtype = device.get("deviceType")
        if dtype in DEVICE_TYPE_THERMOSTATS or _is_analog_mode(device):
            entities.append(EOBTimezoneSelect(coordinator, device))
    if entities:
        async_add_entities(entities)


class EOBTimezoneSelect(CoordinatorEntity, SelectEntity):
    _attr_options = TIMEZONE_OPTIONS
    _attr_unique_id = "eob_wifi_timezone_{}"

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_timezone_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Timezone"
        dtype = device.get("deviceType")
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=device.get("name", f"EOB {self._device_id}"),
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_NAMES.get(dtype, f"Type {dtype}"),
            sw_version=device.get("firmwareVersionStringFromDevice"),
        )

    @property
    def _device(self) -> dict | None:
        if not self.coordinator.data:
            return None
        for d in self.coordinator.data.get("devices", []):
            if d.get("deviceId") == self._device_id:
                return d
        return None

    @property
    def current_option(self) -> str | None:
        d = self._device
        if not d:
            return None
        settings = d.get("thermSettings")
        if not isinstance(settings, dict):
            return None
        tz_index = settings.get("timeZone")
        if tz_index is None:
            return None
        try:
            idx = int(tz_index)
            if 0 <= idx < len(TIMEZONE_OPTIONS):
                return TIMEZONE_OPTIONS[idx]
        except (ValueError, TypeError):
            pass
        return None

    async def async_select_option(self, option: str) -> None:
        if option not in TIMEZONE_OPTIONS:
            return
        tz_index = TIMEZONE_OPTIONS.index(option)
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_timezone(self._device_id, tz_index)
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("thermSettings", {})["timeZone"] = tz_index
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
