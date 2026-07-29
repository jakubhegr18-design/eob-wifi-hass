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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import (
    DEVICE_TYPE_NAMES,
    DEVICE_TYPE_TS11_WIFI,
    DEVICE_TYPE_U2,
    DEVICE_TYPE_PT14,
    DEVICE_TYPE_PT14_WIF_ONLY,
    DOMAIN,
    MANUFACTURER,
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
        dtype = device.get("deviceType")
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=device.get("name", f"EOB {self._device_id}"),
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_NAMES.get(dtype, f"Type {dtype}"),
            sw_version=device.get("firmwareVersionStringFromDevice"),
        )

    def _get_therm_data(self) -> dict:
        return self._device.get("thermData") or {}

    def _get_therm_settings(self) -> dict:
        return self._device.get("thermSettings") or {}

    def _get_device_data(self) -> dict:
        return self._device.get("deviceData") or {}

    @property
    def current_temperature(self) -> float | None:
        return self._get_therm_data().get("actualTemp")

    @property
    def target_temperature(self) -> float | None:
        return self._get_therm_data().get("desiredTemp")

    @property
    def hvac_mode(self) -> HVACMode | None:
        device_data = self._get_device_data()
        if device_data.get("isSwitchedOn") is False:
            return HVACMode.OFF
        therm = self._get_therm_settings()
        if therm.get("isAuto") is True:
            return HVACMode.AUTO
        return HVACMode.HEAT

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_thermostat_temp(self._device_id, temp)
        if ok:
            therm = self._get_therm_data()
            therm["desiredTemp"] = temp
            self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode = HVAC_MAP_REVERSE.get(hvac_mode, MODE_AUTO)
        mqtt = self.coordinator.mqtt_manager

        if mode == MODE_AUTO:
            ok = await mqtt.set_device_mode(self._device_id, MODE_AUTO)
        elif mode == MODE_OFF:
            ok = await mqtt.set_device_mode(self._device_id, MODE_OFF)
        else:
            desired = self._get_therm_data().get("desiredTemp", 21)
            ok = await mqtt.set_thermostat_temp(self._device_id, desired)

        if ok:
            device_data = self._get_device_data()
            if mode == MODE_OFF:
                device_data["isSwitchedOn"] = False
            else:
                device_data["isSwitchedOn"] = True
            settings = self._get_therm_settings()
            settings["isAuto"] = mode == MODE_AUTO
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
        self._attr_unique_id = f"eob_wifi_switch_{self._device_id}"
        self._attr_name = device.get("name", f"EOB Switch {self._device_id}")
        dtype = device.get("deviceType")
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=device.get("name", f"EOB {self._device_id}"),
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_NAMES.get(dtype, f"Type {dtype}"),
            sw_version=device.get("firmwareVersionStringFromDevice"),
        )

    def _get_device_data(self) -> dict:
        return self._device.get("deviceData") or {}

    @property
    def hvac_mode(self) -> HVACMode | None:
        is_on = self._get_device_data().get("isSwitchedOn", False)
        return HVACMode.HEAT if is_on else HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        turn_on = hvac_mode == HVACMode.HEAT
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_relay_state(self._device_id, turn_on)
        if ok:
            device_data = self._get_device_data()
            device_data["isSwitchedOn"] = turn_on
            self.async_write_ha_state()
