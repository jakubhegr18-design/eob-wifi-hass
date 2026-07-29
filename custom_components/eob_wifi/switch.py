from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
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
        if dtype not in DEVICE_TYPE_THERMOSTATS and not _is_analog_mode(device):
            entities.append(EOBSwitch(coordinator, device))
    if entities:
        async_add_entities(entities)


class EOBSwitch(CoordinatorEntity, SwitchEntity):

    def __init__(
        self, coordinator: EOBWifiCoordinator, device: dict
    ) -> None:
        super().__init__(coordinator)
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

    @property
    def _device(self) -> dict | None:
        if not self.coordinator.data:
            return None
        devices = self.coordinator.data.get("devices", [])
        for d in devices:
            if d.get("deviceId") == self._device_id:
                return d
        return None

    def _get_device_data(self) -> dict:
        d = self._device
        if not d:
            return {}
        return d.get("deviceData") or {}

    @property
    def is_on(self) -> bool | None:
        return self._get_device_data().get("isSwitchedOn")

    async def async_turn_on(self, **kwargs) -> None:
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_relay_state(self._device_id, True)
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("deviceData", {})["isSwitchedOn"] = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        mqtt = self.coordinator.mqtt_manager
        ok = await mqtt.set_relay_state(self._device_id, False)
        if ok:
            d = self._device
            if d is not None:
                d.setdefault("deviceData", {})["isSwitchedOn"] = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
