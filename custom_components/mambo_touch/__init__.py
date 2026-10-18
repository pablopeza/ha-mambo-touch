"""Cecotec Mambo Touch food processor over the KitchenIdea MQTT broker."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .client import MamboClient
from .const import CONF_DEVICE_ID

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SENSOR]

type MamboConfigEntry = ConfigEntry[MamboClient]


async def async_setup_entry(hass: HomeAssistant, entry: MamboConfigEntry) -> bool:
    data = entry.data
    client = MamboClient(hass, entry.entry_id, data[CONF_HOST], data[CONF_PORT],
                         data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_DEVICE_ID])
    await hass.async_add_executor_job(client.connect)
    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MamboConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await hass.async_add_executor_job(entry.runtime_data.stop)
    return unloaded
