"""Tests for the envelope builder and parser.

Run with: python3 -m unittest discover -s tests
"""

import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "protocol", ROOT / "custom_components" / "mambo_touch" / "protocol.py")
p = importlib.util.module_from_spec(spec)
sys.modules["protocol"] = p
spec.loader.exec_module(p)

TS = 0x652F_8A3C
CAPTURE = json.loads((ROOT / "tests" / "fixtures" / "capture-idle.json").read_text())


class Build(unittest.TestCase):
    def test_start_button(self):
        # 02 02 00 00 00 = start, as captured from the app
        pkt = p.button(p.BTN_START, TS)
        self.assertEqual(pkt[:6], bytes.fromhex("550101100005"))
        self.assertEqual(pkt[6:11], bytes.fromhex("0202000000"))
        self.assertEqual(pkt[11:15], struct.pack("!I", TS))
        self.assertEqual(pkt[-1], sum(pkt[:-1]) & 0xFF)

    def test_buttons_match_capture(self):
        for value, tail in ((p.BTN_START, "00"), (p.BTN_PAUSE, "01"), (p.BTN_STOP, "02")):
            pkt = p.button(value, TS)
            self.assertEqual(pkt[6:11].hex(), "02020000" + tail)

    def test_timer(self):
        # 09 05 00 05 "120.0"
        pkt = p.number(p.F_TIMER, 120, TS)
        self.assertEqual(pkt[6:10], bytes.fromhex("09050005"))
        self.assertEqual(pkt[10:15], b"120.0")
        # 09 05 00 03 "0.0"
        self.assertEqual(p.number(p.F_TIMER, 0, TS)[6:13], bytes.fromhex("09050003") + b"0.0")

    def test_ui(self):
        self.assertEqual(p.number(p.F_UI, 3, TS)[6:13], bytes.fromhex("04050003") + b"3.0")

    def test_params_key_order(self):
        pkt = p.params(1, 6, 40, 0, TS)
        js = b'{"type":"1","speed":"1","time":0,"firepower":6,"temperature":40}'
        self.assertEqual(pkt[6:10], bytes([0x0F, 0x16, 0x00, len(js)]))
        self.assertEqual(pkt[10:10 + len(js)], js)
        self.assertEqual(pkt[5], 4 + len(js))

    def test_matches_mambo_ctl(self):
        # Same bytes as scripts/mambo/mambo_ctl.py in the sacho repo, which
        # was checked against a capture byte by byte.
        def ctl_packet(fld, ts):
            body = bytes([0x55, 0x01, 0x01, 0x10, 0x00, len(fld)]) + fld
            body += struct.pack("!I", ts)
            return body + bytes([sum(body) & 0xFF])

        js = json.dumps({"type": "1", "speed": "1", "time": 0, "firepower": 6,
                         "temperature": 40}, separators=(",", ":")).encode()
        self.assertEqual(p.params(1, 6, 40, 0, TS),
                         ctl_packet(bytes([0x0F, 0x16, 0x00, len(js)]) + js, TS))
        self.assertEqual(p.button(p.BTN_STOP, TS),
                         ctl_packet(bytes([0x02, 0x02, 0x00, 0x00, 0x02]), TS))
        self.assertEqual(p.number(p.F_TIMER, 60, TS),
                         ctl_packet(bytes([0x09, 0x05, 0x00, 0x04]) + b"60.0", TS))

    def test_sequences(self):
        start = p.start_sequence(1, 6, 40, 120, TS)
        self.assertEqual([x[6] for x in start], [0x0F, 0x09, 0x02, 0x04])
        stop = p.stop_sequence(TS)
        self.assertEqual([x[6] for x in stop], [0x02, 0x04, 0x09])
        self.assertEqual(stop[0][10], p.BTN_STOP)


class Parse(unittest.TestCase):
    def test_roundtrip(self):
        fields = p.parse_fields(p.number(p.F_TIMER, 120, TS))
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].fid, p.F_TIMER)
        self.assertEqual(fields[0].as_number(), 120.0)

    def test_bad_checksum(self):
        pkt = bytearray(p.button(p.BTN_STOP, TS))
        pkt[-1] ^= 0xFF
        self.assertEqual(p.parse_fields(bytes(pkt)), [])

    def test_long_json(self):
        # A status report is longer than 255 bytes: the length is 16-bit.
        data = {"runStatus": 3, "cookTime": 118, "temperature": 40, "speed": "1",
                "firepower": 6, "errorCode": 0, "pad": "x" * 400}
        pkt = p.envelope(p.field(p.F_STATUS, p.T_JSON, json.dumps(data)), TS)
        fields = p.parse_fields(pkt)
        self.assertEqual(fields[0].as_json()["cookTime"], 118)

    def test_state_from_status(self):
        s = p.MamboState()
        report = {"dialogStatus": 1, "runStatus": 3, "cookTime": 118, "temperature": 40,
                  "speed": "1", "firepower": 6, "errorCode": 0, "realTimeTemp": "38.5"}
        self.assertTrue(s.apply(p.envelope(p.field(p.F_STATUS, p.T_JSON, json.dumps(report)), TS)))
        self.assertEqual(s.status, "cooking")
        self.assertEqual((s.remaining, s.temperature, s.speed, s.firepower), (118, 40, 1, 6))
        self.assertEqual(s.current_temperature, 38.5)
        self.assertFalse(s.apply(p.envelope(p.field(p.F_STATUS, p.T_JSON, json.dumps(report)), TS)))

    def test_state_real_temp_field(self):
        # a1 05 00 04 "42.0" = current temperature
        s = p.MamboState()
        self.assertTrue(s.apply(p.number(p.F_REAL_TEMP, 42, TS)))
        self.assertEqual(s.current_temperature, 42.0)

    def test_stopped_clears_remaining(self):
        s = p.MamboState(remaining=50)
        s.apply(p.envelope(p.field(p.F_STATUS, p.T_JSON, json.dumps({"runStatus": 1, "cookTime": 50})), TS))
        self.assertEqual(s.status, "stopped")
        self.assertEqual(s.remaining, 0)

    def test_fallback_json(self):
        s = p.MamboState()
        s.apply(b'\x00\x01garbage{"dialogStatus":1,"runStatus":5,"cookTime":30}')
        self.assertEqual(s.status, "paused")
        self.assertEqual(s.remaining, 30)

    def test_button_roundtrip(self):
        fields = p.parse_fields(p.button(p.BTN_PAUSE, TS))
        self.assertEqual((fields[0].fid, fields[0].value), (p.F_BUTTON, b"\x01"))

    def test_capture_checksums(self):
        for key, hexstr in CAPTURE.items():
            if key.startswith("_"):
                continue
            self.assertTrue(p.parse_fields(bytes.fromhex(hexstr)), key)

    def test_capture_status(self):
        s = p.MamboState()
        self.assertTrue(s.apply(bytes.fromhex(CAPTURE["status"])))
        self.assertEqual(s.status, "stopped")
        self.assertEqual((s.temperature, s.speed, s.firepower, s.remaining, s.error_code),
                         (0, 0, 0, 0, 0))
        self.assertEqual(s.turbo, False)
        self.assertEqual(s.raw["statusSeq"], 30)

    def test_capture_real_temp(self):
        s = p.MamboState()
        s.apply(bytes.fromhex(CAPTURE["real_temp"]))
        self.assertEqual(s.current_temperature, 30.0)

    def test_capture_params_echo(self):
        s = p.MamboState(temperature=40, speed=1, firepower=6, timer=120)
        s.apply(bytes.fromhex(CAPTURE["params_echo"]))
        self.assertEqual((s.temperature, s.speed, s.firepower, s.timer), (0, 0, 0, 0))

    def test_ignores_unrelated_json(self):
        s = p.MamboState()
        self.assertFalse(s.apply(p.params(1, 6, 40, 0, TS)))


if __name__ == "__main__":
    unittest.main()
