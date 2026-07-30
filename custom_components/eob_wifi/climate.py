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
    ATTR_IS_ANALOG_MODE,
    DEVICE_TYPE_NAMES,
    DEVICE_TYPE_THERMOSTATS,
    DOMAIN,
    MANUFACTURER,
    MODE_AUTO,
    MODE_MANU,
    MODE_OFF,
    _is_analog_mode,
)

_LOGGER = logging.getLogger(__name__)

HVAC_MAP = {
    MODE_AUTO: HVACMode.AUTO,
    MODE_MANU: HVACMode.HEAT,
    MODE_OFF: HVACMode.OFF,
}

HVAC_MAP_REVERSE = {v: k for k, v in HVAC_MAP.items()}


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
            entities.append(EOBThermostat(coordinator, device))
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

    @property
    def _device(self) -> dict | None:
        if not self.coordinator.data:
            return None
        devices = self.coordinator.data.get("devices", [])
        for d in devices:
            if d.get("deviceId") == self._device_id:
                return d
        return None

    def _get_therm_data(self) -> dict:
        d = self._device
        if not d:
            return {}
        val = d.get("thermData")
        if isinstance(val, dict) and val:
            return val
        return d.get("thermSettings") or {}

    def _get_therm_settings(self) -> dict:
        d = self._device
        if not d:
            return {}
        val = d.get("thermSettings")
        return val if isinstance(val, dict) else {}

    def _get_is_analog_mode(self) -> bool:
        d = self._device
        if not d:
            return False
        therm = d.get("thermData")
        return bool(therm.get(ATTR_IS_ANALOG_MODE)) if isinstance(therm, dict) else False

    def _get_device_data(self) -> dict:
        d = self._device
        if not d:
            return {}
        val = d.get("deviceData")
        return val if isinstance(val, dict) else {}

    @staticmethod
    def _to_float(val) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    @property
    def current_temperature(self) -> float | None:
        return self._to_float(self._get_therm_data().get("actualTemp"))

    @property
    def target_temperature(self) -> float | None:
        return self._to_float(self._get_therm_data().get("desiredTemp"))

    @property
    def hvac_mode(self) -> HVACMode | None:
        device_data = self._get_device_data()
        if device_data.get("isSwitchedOn") is False:
            return HVACMode.OFF
        therm = self._get_therm_settings()
        if therm.get("isAuto") is True:
            return HVACMode.AUTO
        return HVACMode.HEAT

    async def _refresh(self) -> None:
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self._device
        if not d:
            return {}
        attrs = {}
        mqtt_state = d.get("mqttState")
        if mqtt_state:
            attrs["mqtt_raw_state"] = mqtt_state
        therm = self._get_therm_data()
        if isinstance(therm, dict):
            for key in ("unknown_2", "unknown_3"):
                if key in therm:
                    attrs[key] = therm[key]
        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return

        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_thermostat_temp(self._device_id, temp, self._get_is_analog_mode())
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("thermData", {})["desiredTemp"] = temp
            self.async_write_ha_state()
            await self._refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode = HVAC_MAP_REVERSE.get(hvac_mode, MODE_AUTO)
        mqtt = self.coordinator.mqtt_manager

        if mode == MODE_AUTO:
            ok = await mqtt.set_device_mode(self._device_id, MODE_AUTO)
        elif mode == MODE_OFF:
            ok = await mqtt.set_device_mode(self._device_id, MODE_OFF)
        else:
            desired = self._get_therm_data().get("desiredTemp", 21)
            ok = await mqtt.set_thermostat_temp(self._device_id, desired, self._get_is_analog_mode())

        if ok:
            d = self._device
            if d is not None:
                dd = d.setdefault("deviceData", {})
                dd["isSwitchedOn"] = mode != MODE_OFF
                d.setdefault("thermSettings", {})["isAuto"] = mode == MODE_AUTO
            self.async_write_ha_state()
            await self._refresh()
