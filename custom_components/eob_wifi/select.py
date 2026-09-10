"""Select entities for EOB WiFi devices - empty until timezone protocol is known.

TODO: Add EOBTimezoneSelect here once HAR capture of the official app reveals
the MQTT write format for the timezone field (needs new publish method + read
of the timezone field). Add Platform.SELECT back to PLATFORMS in __init__.py.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    pass
