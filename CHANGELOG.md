# Changelog

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
- Mambo HUD Card: jar that shows what the robot is doing (blades spin with
  the speed, steam while heating), big clock with the time left or the timer,
  current temperature, start / pause / resume / stop, temperature and timer
  steppers, speed and heat power selectors, error and connection banner.
  Starting with heat takes two taps. Visual editor that pre-fills the
  integration's entities. Light and dark themes, English and Spanish.
