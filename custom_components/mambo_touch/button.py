"""Buttons: start, pause, resume and stop."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MamboConfigEntry
from .client import MamboClient
from .entity import MamboEntity

# key -> client method
BUTTONS = {"start": "cook", "pause": "pause", "resume": "resume", "stop": "halt"}


async def async_setup_entry(hass: HomeAssistant, entry: MamboConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(MamboButton(entry.runtime_data, key) for key in BUTTONS)


class MamboButton(MamboEntity, ButtonEntity):
    def __init__(self, client: MamboClient, key: str) -> None:
        super().__init__(client, key)
        self._method = BUTTONS[key]

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(getattr(self.client, self._method))
