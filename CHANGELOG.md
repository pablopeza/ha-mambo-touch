# Changelog

## 0.1.1

### Fixed

- Start did nothing when the robot was on its home screen: it only takes the
  cooking parameters on the manual cooking screen and ignores them anywhere
  else. Start now waits for the robot to echo the parameters back; if they
  don't come, it opens manual cooking (a start on the home screen does just
  that) and sends them again, or fails with a clear error. If that start
  turns out to begin a cook without our timer, it stops it.
- Status and time left stayed still during a cook: the robot sends the
  countdown (field `0d`) and the run state (field `02`) on their own, and the
  full report only when asked. Both are read now, and the full report is
  asked for on connect, after every command and every 5 minutes (`1f {}`).
- The set points dropped to 0 after every cook: at the end the robot resets
  its parameters (an echo with `duration`) just before it says it stopped,
  and that reset was taken as a change made on the robot.

### Added

- `probe_temperature` attribute on the status sensor (field `0e`).

## 0.1.0

First version, not published yet.

### Added

- `mambo_touch` integration: its own MQTT 5 connection to the KitchenIdea
  broker the robot uses (random client id, never the robot's), set up from
  the UI (broker, port, username, password, device id).
- Sensors: status (stopped / cooking / paused), current temperature, time
  left, error code; broker connection binary sensor.
- Set points as `number` entities: target temperature (0 or 37-120 °C), speed
  (0-10), heat power (1-10, follows the temperature unless changed) and timer
  (up to 12 h). They're restored after a restart and sent when the cook
  starts; while it runs, temperature, speed and heat power changes go to the
  robot straight away, like in the app.
- Buttons: start, pause, resume and stop. Start refuses to run without a
  timer or with a temperature below 37 °C.
- Pairs with the [Mambo HUD Card](https://github.com/pablopeza/mambo-hud-card).
