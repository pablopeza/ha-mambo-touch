"""Sensors: status, current temperature, time left and error code."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MamboConfigEntry
from .client import MamboClient
from .entity import MamboEntity
from .protocol import RUN_STATES


@dataclass(frozen=True, kw_only=True)
class MamboSensorDescription(SensorEntityDescription):
    value: Callable[[MamboClient], Any]


SENSORS = (
    MamboSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[*RUN_STATES.values(), "unknown"],
        value=lambda c: c.state.status,
    ),
    MamboSensorDescription(
        key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=0,
        value=lambda c: c.state.current_temperature,
    ),
    MamboSensorDescription(
        key="remaining_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value=lambda c: c.state.remaining,
    ),
    MamboSensorDescription(
        key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda c: c.state.error_code,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: MamboConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(MamboSensor(entry.runtime_data, d) for d in SENSORS)


class MamboSensor(MamboEntity, SensorEntity):
    entity_description: MamboSensorDescription

    def __init__(self, client: MamboClient, description: MamboSensorDescription) -> None:
        super().__init__(client, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value(self.client)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key != "status":
            return None
        s = self.client.state
        # probe_temperature: field 0e, rises fast while heating (base or
        # heater?, not known yet).
        return {"run_status": s.run_status, "turbo": s.turbo, "speed": s.speed,
                "temperature": s.temperature, "firepower": s.firepower,
                "probe_temperature": s.probe_temperature}
