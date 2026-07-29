from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import (
    DEVICE_TYPE_TS11_WIFI,
    DEVICE_TYPE_U2,
    DEVICE_TYPE_PT14,
    DEVICE_TYPE_PT14_WIF_ONLY,
    DOMAIN,
    MODE_AUTO,
    MODE_MANU,
    MODE_OFF,
)

_LOGGER = logging.getLogger(__name__)

HVAC_MAP = {
    MODE_AUTO: HVACMode.AUTO,
    MODE_MANU: HVACMode.HEAT,
    MODE_OFF: HVACMode.OFF,
}

HVAC_MAP_REVERSE = {v: k for k, v in HVAC_MAP.items()}

THERMOSTAT_TYPES = [
    DEVICE_TYPE_TS11_WIFI,
    DEVICE_TYPE_U2,
]

RELAY_TYPES = [
    DEVICE_TYPE_PT14,
    DEVICE_TYPE_PT14_WIF_ONLY,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EOBWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices:
        dtype = device.get("deviceType")
        if dtype in THERMOSTAT_TYPES:
            entities.append(EOBThermostat(coordinator, device))
        elif dtype in RELAY_TYPES:
            entities.append(EOBSwitch(coordinator, device))
    if entities:
        async_add_entities(entities)


class EOBThermostat(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]
    _attr_max_temp = 39
    _attr_min_temp = 3
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_{self._device_id}"
        self._attr_name = device.get("name", f"EOB Thermostat {self._device_id}")
        self._attr_device_id = self._device_id

    @property
    def current_temperature(self) -> float | None:
        return self._device.get("currentTemperature")

    @property
    def target_temperature(self) -> float | None:
        return self._device.get("desiredTemp")

    @property
    def hvac_mode(self) -> HVACMode | None:
        mode = self._device.get("mode", MODE_AUTO)
        return HVAC_MAP.get(mode, HVACMode.AUTO)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        payload = {
            "deviceId": self._device_id,
            "desiredTemp": temp,
            "mode": HVAC_MAP_REVERSE.get(self.hvac_mode, MODE_AUTO),
        }
        ok = await self.coordinator.send_command(payload)
        if ok:
            self._device["desiredTemp"] = temp
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode = HVAC_MAP_REVERSE.get(hvac_mode, MODE_AUTO)
        payload: dict[str, Any] = {
            "deviceId": self._device_id,
            "mode": mode,
        }
        if mode == MODE_MANU:
            payload["desiredTemp"] = self._device.get(
                "desiredTemp", 21
            )
        ok = await self.coordinator.send_command(payload)
        if ok:
            self._device["mode"] = mode
            self.async_write_ha_state()


class EOBSwitch(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature(0)

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_{self._device_id}"
        self._attr_name = device.get("name", f"EOB Switch {self._device_id}")

    @property
    def hvac_mode(self) -> HVACMode | None:
        is_on = self._device.get("isOutputOn", False)
        return HVACMode.HEAT if is_on else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        payload = {
            "deviceId": self._device_id,
            "isOutputOn": hvac_mode == HVACMode.HEAT,
        }
        ok = await self.coordinator.send_command(payload)
        if ok:
            self._device["isOutputOn"] = hvac_mode == HVACMode.HEAT
            self.async_write_ha_state()
