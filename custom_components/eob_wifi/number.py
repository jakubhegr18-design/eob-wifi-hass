"""Number entities for EOB WiFi devices - TS11 Therm settings."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import (
    ATTENUATION_TEMP_DEFAULT,
    COMFORTABLE_TEMP_DEFAULT,
    DEVICE_TYPE_NAMES,
    DEVICE_TYPE_THERMOSTATS,
    DOMAIN,
    MANUFACTURER,
    TEMP_MAX,
    TEMP_MIN,
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
            entities.append(EOBAttenuationTemperature(coordinator, device))
            entities.append(EOBComfortableTemperature(coordinator, device))
    if entities:
        async_add_entities(entities)


class _EOBNumberBase(CoordinatorEntity, NumberEntity):
    _attr_native_min_value = TEMP_MIN
    _attr_native_max_value = TEMP_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("deviceId")
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

    def _get_therm_settings(self) -> dict:
        d = self._device
        if not d:
            return {}
        val = d.get("thermSettings")
        return val if isinstance(val, dict) else {}

    @staticmethod
    def _to_float(val) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None


class EOBAttenuationTemperature(_EOBNumberBase):
    _attr_unique_id = "eob_wifi_attenuation_temperature_{}"
    _attr_translation_key = "attenuation_temperature"

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"eob_wifi_attenuation_temperature_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Attenuation Temperature"

    @property
    def native_value(self) -> float | None:
        settings = self._get_therm_settings()
        val = settings.get("attenuationTemperature")
        return self._to_float(val)

    async def async_set_native_value(self, value: float) -> None:
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_attenuation_temperature(self._device_id, value)
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("thermSettings", {})["attenuationTemperature"] = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()


class EOBComfortableTemperature(_EOBNumberBase):
    _attr_unique_id = "eob_wifi_comfortable_temperature_{}"
    _attr_translation_key = "comfortable_temperature"

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"eob_wifi_comfortable_temperature_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Comfortable Temperature"

    @property
    def native_value(self) -> float | None:
        settings = self._get_therm_settings()
        val = settings.get("comfortableTemperature")
        return self._to_float(val)

    async def async_set_native_value(self, value: float) -> None:
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_comfortable_temperature(self._device_id, value)
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("thermSettings", {})["comfortableTemperature"] = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
