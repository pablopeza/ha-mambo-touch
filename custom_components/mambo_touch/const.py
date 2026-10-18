"""Constants for the Mambo Touch integration."""

DOMAIN = "mambo_touch"

CONF_DEVICE_ID = "device_id"

DEFAULT_HOST = "3.71.50.36"
DEFAULT_PORT = 1883

# Ranges from the Mambo Touch manual: temperature 37-120 °C (0 = no heat),
# speed 0-10, heat power 1-10 (only with temperature), timer up to 12 h.
TEMP_MIN = 37
TEMP_MAX = 120
SPEED_MAX = 10
POWER_MAX = 10
TIMER_MAX = 12 * 3600

# Defaults for a new install: warm, gentle, short.
DEFAULT_SETPOINTS = {"temperature": 0, "speed": 1, "firepower": 0, "timer": 60}

# Pause between the packets of a sequence, like the app.
SEND_GAP = 0.4

SIGNAL_UPDATE = f"{DOMAIN}_update_{{}}"
