"""Number entities for EOB WiFi devices - TS11 Therm settings (read-only)."""
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
    _attr_translation_key = None

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

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"eob_wifi_attenuation_temperature_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Attenuation Temperature"
        self._attr_native_value = ATTENUATION_TEMP_DEFAULT

    @property
    def native_value(self) -> float | None:
        settings = self._get_therm_settings()
        val = settings.get("attenuationTemperature")
        result = self._to_float(val)
        if result is not None:
            self._attr_native_value = result
        return self._attr_native_value


class EOBComfortableTemperature(_EOBNumberBase):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator, device)
        self._attr_unique_id = f"eob_wifi_comfortable_temperature_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Comfortable Temperature"
        self._attr_native_value = COMFORTABLE_TEMP_DEFAULT

    @property
    def native_value(self) -> float | None:
        settings = self._get_therm_settings()
        val = settings.get("comfortableTemperature")
        result = self._to_float(val)
        if result is not None:
            self._attr_native_value = result
        return self._attr_native_value
