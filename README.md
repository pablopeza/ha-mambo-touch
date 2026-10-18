# Mambo Touch for Home Assistant

A Home Assistant integration for the **Cecotec Mambo Touch** food processor:
status, time left, temperature, start / pause / resume / stop, and the
temperature, speed, heat power and timer set points. Recipes are out of scope.

Pair it with the [Mambo HUD Card](https://github.com/pablopeza/mambo-hud-card)
for an instrument-panel dashboard card.

> ⚠️ **This is a heating appliance with blades.** The card asks for a second
> tap before it starts a cook with heat, and the integration won't start
> without a timer, but nobody can see the jar from a dashboard. Only start it
> when someone is next to it, and with the lid on.

## How it works

The Mambo Touch has no local API: it only talks to the KitchenIdea cloud over
**MQTT 5 without TLS**. The `mambo_touch` integration logs in to the same
broker with the robot's MQTT credentials and its **own random client id**
(using the robot's id would kick the robot off), listens to the robot's
reports and sends the same binary commands as the official app.

So this needs the cloud, and the credentials have to be captured from the
robot's own traffic first (they're in the MQTT `CONNECT` packet). There is
no account login.

## Installation

### Via HACS

1. HACS → **⋮** menu (top right) → **Custom repositories**
2. URL: `https://github.com/pablopeza/ha-mambo-touch`, category **Integration**
3. Search for **"Mambo Touch"** in HACS → Download, and restart Home Assistant

### Manual

Copy `custom_components/mambo_touch` to `config/custom_components/` and
restart Home Assistant.

### Set up

Settings → Devices & services → Add integration → **Mambo Touch**: broker
(`3.71.50.36`), port (`1883`), username, password and the robot's device id
(`mboTouch…`).

For the dashboard, use the [Mambo HUD Card](https://github.com/pablopeza/mambo-hud-card).

## Entities

| Entity | Notes |
|---|---|
| `sensor.*_status` | `stopped`, `cooking`, `paused`; `unknown` until the robot reports (it says nothing while idle) |
| `sensor.*_temperature` | Current temperature of the jar |
| `sensor.*_time_left` | Seconds left of the running cook |
| `sensor.*_error_code` | 0 = no error (diagnostic) |
| `binary_sensor.*_broker_connection` | Connection to the broker (diagnostic) |
| `number.*_target_temperature` | 0 = no heat, else 37-120 °C |
| `number.*_speed` | 0-10 |
| `number.*_heat_power` | 1-10, only with heat. Set from the temperature (40 °C → 4) unless changed |
| `number.*_timer` | Seconds, up to 12 h. Needed to start |
| `button.*_start` / `_pause` / `_resume` / `_stop` | |

The set points live in Home Assistant until the cook starts. While a cook
runs, changes to temperature, speed and heat power are sent to the robot at
once (the timer isn't); if someone turns the knob on the robot, the set
points follow it.

## Protocol

Every message is `55 01 01 <class> <len:2> <field> <ts:4> <sum:1>`, where the
field is `<id> <type> <len:2> <value>` and the last byte is the sum of all the
previous ones modulo 256. Commands go to `kitchenidea/U/D/<device id>` and
reports come on `kitchenidea/D/P/<device id>`. Details and the captured
messages are in [`protocol.py`](custom_components/mambo_touch/protocol.py)
and [`tests/`](tests).

The robot only takes the cooking parameters on its **manual cooking screen**;
anywhere else it ignores them. Start waits for the robot to echo them back
and, if they don't come, opens that screen first.

Still unconfirmed on the real robot: **resume** (`02 02 00 00 00`, the same
as start) and set point changes during a cook.

## Tests

```bash
python3 -m unittest discover -s tests   # protocol tests run anywhere
```

The client tests need Home Assistant installed (they're skipped otherwise);
they never publish anything.

## License

MIT
