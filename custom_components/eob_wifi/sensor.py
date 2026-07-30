from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EOBWifiCoordinator
from .const import DEVICE_TYPE_NAMES, DEVICE_TYPE_THERMOSTATS, DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EOBWifiCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices:
        entities.append(EOBFirmwareSensor(coordinator, device))
        dtype = device.get("deviceType")
        if dtype in DEVICE_TYPE_THERMOSTATS:
            entities.append(EOBTemperatureSensor(coordinator, device))
            entities.append(EOBTargetTemperatureSensor(coordinator, device))
    if entities:
        async_add_entities(entities)


class EOBFirmwareSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_fw_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Firmware"
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

    @property
    def native_value(self) -> str | None:
        d = self._device
        if not d:
            return None
        return d.get("firmwareVersionStringFromDevice")


class EOBTemperatureSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_temp_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
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

    @property
    def native_value(self) -> float | None:
        d = self._device
        if not d:
            return None
        therm = d.get("thermData")
        if not isinstance(therm, dict):
            return None
        return therm.get("actualTemp")


class EOBTargetTemperatureSensor(CoordinatorEntity, SensorEntity):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device.get("deviceId")
        self._attr_unique_id = f"eob_wifi_target_temp_{self._device_id}"
        self._attr_name = f"{device.get('name', f'EOB {self._device_id}')} Target Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
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

    @property
    def native_value(self) -> float | None:
        d = self._device
        if not d:
            return None
        therm = d.get("thermData")
        if not isinstance(therm, dict):
            return None
        return therm.get("desiredTemp")
