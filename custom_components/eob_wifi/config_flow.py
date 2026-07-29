from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_LOGIN, BASE_SERVER_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                url = f"{BASE_SERVER_URL}{API_LOGIN}"
                async with session.post(
                    url,
                    json={
                        "userName": user_input[CONF_USERNAME],
                        "password": user_input[CONF_PASSWORD],
                    },
                ) as resp:
                    if resp.status != 200:
                        errors["base"] = "invalid_auth"
                    else:
                        return self.async_create_entry(
                            title=f"EOB WiFi ({user_input[CONF_USERNAME]})",
                            data=user_input,
                        )
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
