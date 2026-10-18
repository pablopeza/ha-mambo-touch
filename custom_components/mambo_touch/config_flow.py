"""Config flow: broker login and the robot's device id."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME

from .client import check_connection
from .const import CONF_DEVICE_ID, DEFAULT_HOST, DEFAULT_PORT, DOMAIN


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, DEFAULT_HOST)): str,
        vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): int,
        vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_DEVICE_ID, default=defaults.get(CONF_DEVICE_ID, "")): str,
    })


class MamboConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            user_input[CONF_DEVICE_ID] = device_id
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            error = await self.hass.async_add_executor_job(
                check_connection, user_input[CONF_HOST], user_input[CONF_PORT],
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            if error:
                errors["base"] = error
            else:
                return self.async_create_entry(title="Mambo Touch", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema(user_input or {}),
                                    errors=errors)
