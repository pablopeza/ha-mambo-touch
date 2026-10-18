"""Set points: temperature, speed, heat power and timer.

They are kept here and sent when the cook starts. While a cook runs, a
change goes to the robot straight away (except the timer), like in the app.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntityDescription,
    NumberMode,
    RestoreNumber,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MamboConfigEntry
from .client import MamboClient
from .const import POWER_MAX, SPEED_MAX, TEMP_MAX, TEMP_MIN, TIMER_MAX
from .entity import MamboEntity


@dataclass(frozen=True, kw_only=True)
class MamboNumberDescription(NumberEntityDescription):
    setpoint: str


NUMBERS = (
    MamboNumberDescription(
        key="target_temperature", setpoint="temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0, native_max_value=TEMP_MAX, native_step=1, mode=NumberMode.BOX,
    ),
    MamboNumberDescription(
        key="speed", setpoint="speed",
        native_min_value=0, native_max_value=SPEED_MAX, native_step=1, mode=NumberMode.SLIDER,
    ),
    MamboNumberDescription(
        key="heat_power", setpoint="firepower",
        native_min_value=0, native_max_value=POWER_MAX, native_step=1, mode=NumberMode.SLIDER,
    ),
    MamboNumberDescription(
        key="timer", setpoint="timer",
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0, native_max_value=TIMER_MAX, native_step=1, mode=NumberMode.BOX,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: MamboConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(MamboNumber(entry.runtime_data, d) for d in NUMBERS)


class MamboNumber(MamboEntity, RestoreNumber):
    entity_description: MamboNumberDescription

    def __init__(self, client: MamboClient, description: MamboNumberDescription) -> None:
        super().__init__(client, description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        if last and last.native_value is not None:
            self.client.setpoints[self.entity_description.setpoint] = int(last.native_value)

    @property
    def native_value(self) -> float:
        return self.client.setpoints[self.entity_description.setpoint]

    async def async_set_native_value(self, value: float) -> None:
        key = self.entity_description.setpoint
        value = int(value)
        if key == "temperature" and 0 < value < TEMP_MIN:
            raise ServiceValidationError(f"Temperature must be 0 or {TEMP_MIN}-{TEMP_MAX} °C")
        await self.hass.async_add_executor_job(self.client.set_point, key, value)
        # Heat power follows the temperature: refresh every set point.
        self.client.notify()
