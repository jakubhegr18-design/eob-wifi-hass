from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import DEVICE_TYPE_TS11_WIFI, DEVICE_TYPE_U2, DOMAIN

_LOGGER = logging.getLogger(__name__)

THERMOSTAT_TYPES = [
    DEVICE_TYPE_TS11_WIFI,
    DEVICE_TYPE_U2,
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
            entities.append(EOBActualTempSensor(coordinator, device))
            entities.append(EOBDesiredTempSensor(coordinator, device))
            entities.append(EOBFirmwareSensor(coordinator, device))
    if entities:
        async_add_entities(entities)


class EOBActualTempSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_actual_temp_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Temperature"

    @property
    def native_value(self) -> float | None:
        therm = self._device.get("thermData") or {}
        return therm.get("actualTemp")


class EOBDesiredTempSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_desired_temp_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Target Temperature"

    @property
    def native_value(self) -> float | None:
        therm = self._device.get("thermData") or {}
        return therm.get("desiredTemp")


class EOBFirmwareSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_fw_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Firmware"

    @property
    def native_value(self) -> str | None:
        return self._device.get("firmwareVersionStringFromDevice")
