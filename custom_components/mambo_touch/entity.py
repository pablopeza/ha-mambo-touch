"""Base entity: one device per robot, refreshed on every report."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .client import MamboClient
from .const import DOMAIN


class MamboEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, client: MamboClient, key: str) -> None:
        self.client = client
        self._attr_translation_key = key
        self._attr_unique_id = f"{client.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, client.device_id)},
            name="Mambo Touch",
            manufacturer="Cecotec",
            model="Mambo Touch",
        )

    @property
    def available(self) -> bool:
        return self.client.connected

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(self.hass, self.client.signal, self.async_write_ha_state))
