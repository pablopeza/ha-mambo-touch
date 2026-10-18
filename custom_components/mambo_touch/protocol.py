"""Mambo Touch MQTT protocol: build commands and parse the robot's messages.

Pure Python, no Home Assistant imports, so it can be tested on its own.

Every message is an envelope around one field:

    55 01 01 <class> <len:2> <field> <ts:4> <sum:1>

- `<class>`: 0x10 for commands and most status messages; the robot uses
  other values for its boot messages (0x02 device info, 0x08, ...).
- `<len:2>`: big-endian length of the field.
- the field is `<id> <type> <len:2> <value>`; type 0x16 holds JSON and 0x05 a
  number as text (`"120.0"`). Type 0x02 (buttons) is `<id> 02 00 00 <byte>`:
  its length reads 0 and one byte follows.
- `<ts:4>`: Unix time in seconds, big-endian.
- `<sum:1>`: sum of every previous byte modulo 256 (not a CRC).

Checked against a capture of the robot (18-oct-2026) and the commands sent by
the app.
"""

from __future__ import annotations

import json
import struct
import time
from dataclasses import dataclass, field as dc_field
from typing import Any

HEADER = bytes([0x55, 0x01, 0x01])
CLASS_COMMAND = 0x10

# Field ids
F_BUTTON = 0x02  # 00 start/resume, 01 pause, 02 stop; the robot reports "0.0" / "2.0"
F_UI = 0x04  # "3.0" after start, "1.0" after stop
F_TIMER = 0x09  # timer in seconds, "120.0"
F_COUNTDOWN = 0x0D  # robot: seconds left, every second while cooking
F_PROBE = 0x0E  # robot: second temperature, rises while heating
F_PARAMS = 0x0F  # manual cooking parameters (JSON), both ways
F_QUERY = 0x1F  # "{}" asks the robot for a full status report
F_STATUS = 0xA0  # full status report from the robot (JSON)
F_REAL_TEMP = 0xA1  # current temperature, "42.0"

T_RAW = 0x02
T_NUMBER = 0x05
T_JSON = 0x16

BTN_START = 0x00
BTN_PAUSE = 0x01
BTN_STOP = 0x02

# runStatus values seen on the robot
RUN_STOPPED = 1
RUN_COOKING = 3
RUN_PAUSED = 5
RUN_STATES = {RUN_STOPPED: "stopped", RUN_COOKING: "cooking", RUN_PAUSED: "paused"}


def checksum(data: bytes) -> int:
    return sum(data) & 0xFF


def envelope(fields: bytes, ts: int | None = None, cls: int = CLASS_COMMAND) -> bytes:
    body = HEADER + bytes([cls]) + struct.pack("!H", len(fields)) + fields
    body += struct.pack("!I", int(time.time()) if ts is None else ts)
    return body + bytes([checksum(body)])


def field(fid: int, typ: int, value: str | bytes) -> bytes:
    if isinstance(value, str):
        value = value.encode()
    if typ == T_RAW:
        return bytes([fid, typ, 0x00, 0x00]) + value
    return bytes([fid, typ]) + struct.pack("!H", len(value)) + value


def number_text(value: float) -> str:
    return f"{float(value):.1f}"


def button(value: int, ts: int | None = None) -> bytes:
    return envelope(field(F_BUTTON, T_RAW, bytes([value])), ts)


def number(fid: int, value: float, ts: int | None = None) -> bytes:
    return envelope(field(fid, T_NUMBER, number_text(value)), ts)


def params(speed: int, firepower: int, temperature: int, elapsed: int = 0,
           ts: int | None = None) -> bytes:
    """Manual cooking parameters. The key order matters to the robot."""
    payload = {
        "type": "1",
        "speed": str(int(speed)),
        "time": int(elapsed),
        "firepower": int(firepower),
        "temperature": int(temperature),
    }
    js = json.dumps(payload, separators=(",", ":"))
    return envelope(field(F_PARAMS, T_JSON, js), ts)


def query(ts: int | None = None) -> bytes:
    return envelope(field(F_QUERY, T_JSON, "{}"), ts)


# Button state the robot reports in field 02 -> runStatus
BUTTON_STATES = {0: RUN_COOKING, 1: RUN_PAUSED, 2: RUN_STOPPED}


def start_sequence(speed: int, firepower: int, temperature: int, seconds: int,
                   ts: int | None = None) -> list[bytes]:
    """What the app sends to start a manual cook."""
    return [
        params(speed, firepower, temperature, 0, ts),
        number(F_TIMER, seconds, ts),
        button(BTN_START, ts),
        number(F_UI, 3, ts),
    ]


def stop_sequence(ts: int | None = None) -> list[bytes]:
    return [
        button(BTN_STOP, ts),
        number(F_UI, 1, ts),
        number(F_TIMER, 0, ts),
    ]


@dataclass
class Field:
    fid: int
    typ: int
    value: bytes

    def as_number(self) -> float | None:
        try:
            return float(self.value.decode())
        except (UnicodeDecodeError, ValueError):
            return None

    def as_json(self) -> dict[str, Any] | None:
        try:
            data = json.loads(self.value.decode())
        except (UnicodeDecodeError, ValueError):
            return None
        return data if isinstance(data, dict) else None


def parse_fields(payload: bytes) -> list[Field]:
    """Split an envelope into fields. Returns [] if it isn't one."""
    if len(payload) < 11 or payload[:3] != HEADER:
        return []
    if checksum(payload[:-1]) != payload[-1]:
        return []
    (length,) = struct.unpack("!H", payload[4:6])
    body = payload[6:6 + length]
    if len(body) != length or 6 + length + 5 != len(payload):
        return []
    out: list[Field] = []
    i = 0
    while i + 4 <= len(body):
        fid, typ = body[i], body[i + 1]
        (flen,) = struct.unpack("!H", body[i + 2:i + 4])
        if typ not in (T_NUMBER, T_JSON):
            # Fixed-size types: the rest of the envelope is the value.
            out.append(Field(fid, typ, body[i + 4:]))
            break
        value = body[i + 4:i + 4 + flen]
        if len(value) != flen:
            break
        out.append(Field(fid, typ, value))
        i += 4 + flen
    return out


def find_json(payload: bytes) -> dict[str, Any] | None:
    """Fallback: the outermost JSON object inside a payload."""
    start, end = payload.find(b"{"), payload.rfind(b"}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(payload[start:end + 1])
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


_STATE_KEYS = ("run_status", "temperature", "current_temperature", "probe_temperature",
               "firepower", "speed", "remaining", "timer", "error_code", "turbo")


@dataclass
class MamboState:
    """What the robot last reported. None = not reported yet."""

    run_status: int | None = None
    temperature: int | None = None  # set point, 0 = no heat
    current_temperature: float | None = None
    probe_temperature: float | None = None
    firepower: int | None = None
    speed: int | None = None
    remaining: int | None = None  # cookTime, seconds left
    timer: int | None = None  # set duration, seconds
    error_code: int | None = None
    turbo: bool | None = None
    raw: dict[str, Any] = dc_field(default_factory=dict)

    @property
    def status(self) -> str | None:
        if self.run_status is None:
            return None
        return RUN_STATES.get(self.run_status, "unknown")

    def _snapshot(self) -> tuple:
        return tuple(getattr(self, k) for k in _STATE_KEYS)

    def apply(self, payload: bytes) -> bool:
        """Update from one MQTT payload. True if anything changed."""
        before = self._snapshot()
        fields = parse_fields(payload)
        for f in fields:
            if f.typ == T_JSON:
                data = f.as_json()
                if data is None:
                    continue
                if f.fid == F_PARAMS:
                    self._apply_params(data)
                else:
                    self._apply_status(data)
            elif f.typ == T_NUMBER:
                self._apply_number(f.fid, f.as_number())
        if not fields and b"dialogStatus" in payload:
            data = find_json(payload)
            if data is not None:
                self._apply_status(data)
        return before != self._snapshot()

    def _apply_number(self, fid: int, value: float | None) -> None:
        if value is None:
            return
        if fid == F_REAL_TEMP:
            self.current_temperature = value
        elif fid == F_PROBE:
            self.probe_temperature = value
        elif fid == F_COUNTDOWN:
            self.remaining = int(value)
        elif fid == F_BUTTON and int(value) in BUTTON_STATES:
            self.run_status = BUTTON_STATES[int(value)]
            if self.run_status == RUN_STOPPED:
                self.remaining = 0

    def _apply_params(self, data: dict[str, Any]) -> None:
        # Echo of the manual parameters: {"duration","firepower","speed","temperature"}.
        # Our own command (with "type") is not a report.
        if "type" in data:
            return
        for key, attr in (("temperature", "temperature"), ("firepower", "firepower"),
                          ("speed", "speed"), ("duration", "timer")):
            if key in data:
                setattr(self, attr, _int(data[key]))

    def _apply_status(self, data: dict[str, Any]) -> None:
        # {"dialogStatus":0,"runStatus":1,"cookTime":0,"realTimeTemp":0,...}
        if "runStatus" not in data:
            return
        self.raw = data
        for key, attr in (("runStatus", "run_status"), ("temperature", "temperature"),
                          ("firepower", "firepower"), ("speed", "speed"),
                          ("cookTime", "remaining"), ("errorCode", "error_code")):
            if key in data:
                setattr(self, attr, _int(data[key]))
        if "turbo" in data:
            self.turbo = bool(data["turbo"])
        if "realTimeTemp" in data:
            try:
                self.current_temperature = float(data["realTimeTemp"])
            except (TypeError, ValueError):
                pass
        if self.run_status == RUN_STOPPED:
            self.remaining = 0
