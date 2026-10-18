"""Client logic with a fake broker. Needs Home Assistant installed, so it is
skipped elsewhere. Nothing is ever published: `_send` is replaced.

Run inside the Home Assistant container:
    python3 -m unittest discover -s tests
"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from homeassistant.exceptions import ServiceValidationError
    from custom_components.mambo_touch import protocol as p
    from custom_components.mambo_touch.client import MamboClient, default_power
except ImportError:  # pragma: no cover
    MamboClient = None


class FakeLoop:
    def call_soon_threadsafe(self, *args):
        pass


class FakeHass:
    loop = FakeLoop()


@unittest.skipIf(MamboClient is None, "Home Assistant not installed")
class Client(unittest.TestCase):
    def setUp(self):
        self.c = MamboClient(FakeHass(), "e1", "localhost", 1883, "u", "pw", "mboTouchTEST")
        self.c.connected = True
        self.sent = []
        self.c._send = self.sent.extend

    def receive(self, payload):
        self.c._on_message(None, None, type("M", (), {"payload": payload}))

    def status(self, **kw):
        report = {"dialogStatus": 1, "runStatus": 3, "cookTime": 100, "temperature": 40,
                  "speed": "1", "firepower": 4, "errorCode": "00", "realTimeTemp": 39}
        report.update(kw)
        return p.envelope(p.field(p.F_STATUS, p.T_JSON, json.dumps(report)))

    def test_default_power(self):
        self.assertEqual([default_power(t) for t in (0, 37, 40, 60, 120)], [0, 4, 4, 6, 10])

    def test_start_needs_timer(self):
        self.c.setpoints.update(temperature=40, speed=1, firepower=4, timer=0)
        with self.assertRaises(ServiceValidationError):
            self.c.cook()
        self.assertEqual(self.sent, [])

    def test_start_rejects_low_temperature(self):
        self.c.setpoints.update(temperature=20, timer=60)
        with self.assertRaises(ServiceValidationError):
            self.c.cook()

    def test_start_sequence(self):
        self.c.setpoints.update(temperature=40, speed=1, firepower=6, timer=120)
        self.c.cook()
        self.assertEqual([x[6] for x in self.sent], [0x0F, 0x09, 0x02, 0x04])
        js = p.parse_fields(self.sent[0])[0].as_json()
        self.assertEqual(js, {"type": "1", "speed": "1", "time": 0, "firepower": 6, "temperature": 40})
        self.assertEqual(p.parse_fields(self.sent[1])[0].as_number(), 120.0)

    def test_no_heat_means_no_power(self):
        self.c.setpoints.update(temperature=0, speed=3, firepower=7, timer=30)
        self.c.cook()
        self.assertEqual(p.parse_fields(self.sent[0])[0].as_json()["firepower"], 0)

    def test_setpoint_while_stopped_sends_nothing(self):
        self.c.set_point("temperature", 60)
        self.assertEqual(self.sent, [])
        self.assertEqual(self.c.setpoints["firepower"], 6)

    def test_setpoint_while_cooking_is_sent(self):
        self.receive(self.status())
        self.c.state.timer = 120
        self.c.set_point("speed", 2)
        js = p.parse_fields(self.sent[0])[0].as_json()
        self.assertEqual((js["speed"], js["time"], js["temperature"]), ("2", 20, 40))

    def test_timer_change_while_cooking_not_sent(self):
        self.receive(self.status())
        self.c.set_point("timer", 300)
        self.assertEqual(self.sent, [])

    def test_follows_robot_only_while_running(self):
        self.c.setpoints.update(temperature=80, speed=2, firepower=8, timer=200)
        self.receive(self.status(runStatus=1, temperature=0, speed="0", firepower=0))
        self.assertEqual(self.c.setpoints["temperature"], 80)
        self.receive(self.status())
        self.assertEqual((self.c.setpoints["temperature"], self.c.setpoints["speed"]), (40, 1))

    def test_stop_and_pause(self):
        self.c.halt()
        self.assertEqual(self.sent[0][10], p.BTN_STOP)
        self.sent.clear()
        self.c.pause()
        self.assertEqual(self.sent[0][10], p.BTN_PAUSE)


if __name__ == "__main__":
    unittest.main()
