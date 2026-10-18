"""MQTT connection to the KitchenIdea broker the robot talks to.

The robot only speaks to the cloud broker, so this keeps its own paho client
there (not Home Assistant's MQTT integration, which points at the local
broker). It always uses a random client id: the robot's own id would kick the
robot off the broker.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any

import paho.mqtt.client as mqtt

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_send

from . import protocol as p
from .const import (
    DEFAULT_SETPOINTS,
    POWER_MAX,
    SEND_GAP,
    SIGNAL_UPDATE,
    SPEED_MAX,
    TEMP_MAX,
    TEMP_MIN,
    TIMER_MAX,
)

_LOGGER = logging.getLogger(__name__)


def default_power(temperature: int) -> int:
    """Heat power for a temperature when none was picked (40 °C -> 4)."""
    if temperature <= 0:
        return 0
    return max(1, min(POWER_MAX, round(temperature / 10)))


def new_client_id() -> str:
    return f"ha-mambo-{uuid.uuid4().hex[:10]}"


def check_connection(host: str, port: int, username: str, password: str,
                     timeout: float = 10) -> str | None:
    """Try to log in to the broker. Returns an error key or None. Blocking."""
    done = threading.Event()
    result: dict[str, Any] = {}

    def on_connect(client, userdata, flags, reason_code, properties=None):
        result["rc"] = reason_code
        done.set()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=new_client_id(),
                         protocol=mqtt.MQTTv5)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    try:
        client.connect(host, port, keepalive=20)
    except OSError:
        return "cannot_connect"
    client.loop_start()
    try:
        if not done.wait(timeout):
            return "cannot_connect"
    finally:
        client.loop_stop()
        client.disconnect()
    rc = result["rc"]
    if rc.is_failure:
        return "invalid_auth" if rc.value in (134, 135) else "cannot_connect"
    return None


class MamboClient:
    """One robot: connection, last reported state and the set points."""

    def __init__(self, hass: HomeAssistant, entry_id: str, host: str, port: int,
                 username: str, password: str, device_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.host = host
        self.port = port
        self.device_id = device_id
        self.state = p.MamboState()
        self.setpoints: dict[str, int] = dict(DEFAULT_SETPOINTS)
        self.connected = False
        self.last_seen: float | None = None
        self._lock = threading.Lock()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id=new_client_id(), protocol=mqtt.MQTTv5)
        self._client.username_pw_set(username, password)
        self._client.reconnect_delay_set(min_delay=2, max_delay=120)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    @property
    def signal(self) -> str:
        return SIGNAL_UPDATE.format(self.entry_id)

    @property
    def cmd_topic(self) -> str:
        return f"kitchenidea/U/D/{self.device_id}"

    # --- connection (paho thread) ---

    def connect(self) -> None:
        """Blocking: run in the executor."""
        self._client.connect_async(self.host, self.port, keepalive=30)
        self._client.loop_start()

    def stop(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def notify(self) -> None:
        self.hass.loop.call_soon_threadsafe(async_dispatcher_send, self.hass, self.signal)

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code.is_failure:
            _LOGGER.warning("Mambo broker refused the connection: %s", reason_code)
            return
        # Both topics carry the same reports; D/P is enough.
        client.subscribe(f"kitchenidea/D/P/{self.device_id}", qos=1)
        self.connected = True
        self.notify()

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = False
        self.notify()

    def _on_message(self, client, userdata, msg):
        self.last_seen = time.time()
        with self._lock:
            changed = self.state.apply(msg.payload)
            if changed:
                self._follow_robot()
        if changed:
            self.notify()

    def _follow_robot(self) -> None:
        # While a cook runs the robot is the truth (someone may turn the knob);
        # when it's stopped it reports zeros, which mustn't wipe the set points.
        s = self.state
        if s.run_status not in (p.RUN_COOKING, p.RUN_PAUSED):
            return
        for key, value in (("temperature", s.temperature), ("speed", s.speed),
                           ("firepower", s.firepower), ("timer", s.timer)):
            if value is not None and not (key == "timer" and value == 0):
                self.setpoints[key] = value

    # --- commands (call from the executor) ---

    def _send(self, packets: list[bytes]) -> None:
        if not self.connected:
            raise HomeAssistantError("Not connected to the Mambo broker")
        for i, pkt in enumerate(packets):
            info = self._client.publish(self.cmd_topic, pkt, qos=2)
            info.wait_for_publish(5)
            if i < len(packets) - 1:
                time.sleep(SEND_GAP)

    def _validated(self) -> tuple[int, int, int, int]:
        sp = self.setpoints
        temp, speed, power, timer = sp["temperature"], sp["speed"], sp["firepower"], sp["timer"]
        if timer <= 0:
            raise ServiceValidationError("Set a timer before starting the Mambo")
        if temp and not TEMP_MIN <= temp <= TEMP_MAX:
            raise ServiceValidationError(f"Temperature must be 0 or {TEMP_MIN}-{TEMP_MAX} °C")
        if not 0 <= speed <= SPEED_MAX:
            raise ServiceValidationError(f"Speed must be 0-{SPEED_MAX}")
        power = default_power(temp) if temp and not power else (power if temp else 0)
        return temp, speed, min(power, POWER_MAX), min(timer, TIMER_MAX)

    def cook(self) -> None:
        temp, speed, power, timer = self._validated()
        self._send(p.start_sequence(speed, power, temp, timer))

    def pause(self) -> None:
        self._send([p.button(p.BTN_PAUSE)])

    def resume(self) -> None:
        self._send([p.button(p.BTN_START)])

    def halt(self) -> None:
        self._send(p.stop_sequence())

    def set_point(self, key: str, value: int) -> None:
        """Store a set point; while cooking, send it to the robot as well."""
        sp = self.setpoints
        sp[key] = value
        if key == "temperature":
            sp["firepower"] = default_power(value)
        if self.state.run_status != p.RUN_COOKING or key == "timer":
            return
        # The app sends the time cooked so far with each change.
        elapsed = 0
        if self.state.timer and self.state.remaining is not None:
            elapsed = max(0, self.state.timer - self.state.remaining)
        temp = sp["temperature"]
        power = sp["firepower"] if temp else 0
        self._send([p.params(sp["speed"], power, temp, elapsed)])
