/* Mambo HUD Card — custom Lovelace card for Home Assistant
 * Instrument-panel style card for the Cecotec Mambo Touch food processor:
 * state, time left, current temperature, start / pause / stop, and the
 * temperature, speed, heat power and timer set points in one panel. It uses
 * the entities of the `mambo_touch` integration (in this same repository);
 * every block hides itself when its entities aren't set.
 *
 * Manual install:
 *   copy this file to config/www/, add as a Lovelace resource:
 *     url: /local/mambo-hud-card.js
 *     type: module
 *   then add a card with type: custom:mambo-hud-card
 *
 * UI language follows Home Assistant's configured language automatically.
 * Supported languages: English (en), Spanish (es). Others fall back to
 * English.
 */

const VERSION = "0.1.0";

const STRINGS = {
  en: {
    editor: {
      general: "General",
      status: "Status",
      setpoints: "Set points",
      buttons: "Buttons",
      display: "Display",
      entity: "Status sensor",
      name: "Name (optional)",
      temperature: "Current temperature sensor",
      remaining: "Time left sensor",
      error: "Error code sensor",
      connected: "Broker connection sensor",
      targetTemperature: "Target temperature (number)",
      speed: "Speed (number)",
      power: "Heat power (number)",
      timer: "Timer (number)",
      start: "Start button",
      pause: "Pause button",
      resume: "Resume button",
      stop: "Stop button",
      showControls: "Show control buttons",
      showSetpoints: "Show set points",
    },
    states: {
      stopped: "Stopped",
      cooking: "Cooking",
      paused: "Paused",
      unknown: "Waiting for the robot",
      unavailable: "Unavailable",
    },
    actions: {
      start: "Start",
      pause: "Pause",
      resume: "Resume",
      stop: "Stop",
      confirmHeat: "Heat to {t}? Tap again",
    },
    labels: {
      temperature: "Temperature",
      target: "Target",
      remaining: "Time left",
      timer: "Timer",
      speed: "Speed",
      power: "Heat power",
      noHeat: "No heat",
      powerNeedsHeat: "Set a temperature to pick the heat power",
      error: "Error {c}",
      offline: "No connection to the Mambo broker",
      notFound: "Entity not found",
      speedShort: "Speed",
      powerShort: "Power",
      needsTimer: "Set a timer to start",
    },
  },
  es: {
    editor: {
      general: "General",
      status: "Estado",
      setpoints: "Consignas",
      buttons: "Botones",
      display: "Visualización",
      entity: "Sensor de estado",
      name: "Nombre (opcional)",
      temperature: "Sensor de temperatura actual",
      remaining: "Sensor de tiempo restante",
      error: "Sensor de código de error",
      connected: "Sensor de conexión al broker",
      targetTemperature: "Temperatura objetivo (number)",
      speed: "Velocidad (number)",
      power: "Potencia calorífica (number)",
      timer: "Temporizador (number)",
      start: "Botón de iniciar",
      pause: "Botón de pausar",
      resume: "Botón de reanudar",
      stop: "Botón de parar",
      showControls: "Mostrar botones de control",
      showSetpoints: "Mostrar consignas",
    },
    states: {
      stopped: "Parado",
      cooking: "Cocinando",
      paused: "En pausa",
      unknown: "Esperando al robot",
      unavailable: "No disponible",
    },
    actions: {
      start: "Iniciar",
      pause: "Pausar",
      resume: "Reanudar",
      stop: "Parar",
      confirmHeat: "¿Calentar a {t}? Toca otra vez",
    },
    labels: {
      temperature: "Temperatura",
      target: "Objetivo",
      remaining: "Restante",
      timer: "Temporizador",
      speed: "Velocidad",
      power: "Potencia calorífica",
      noHeat: "Sin calor",
      powerNeedsHeat: "Pon una temperatura para elegir la potencia",
      error: "Error {c}",
      offline: "Sin conexión con el broker del Mambo",
      notFound: "Entidad no encontrada",
      speedShort: "Vel.",
      powerShort: "Pot.",
      needsTimer: "Pon un temporizador para iniciar",
    },
  },
};

// Same palette as the Vacuum and Ecowitt HUD cards, so they sit well together.
const COLORS = {
  info: "#3b82c4",
  low: "#2ba86a",
  moderate: "#c78a00",
  danger: "#d1481c",
  neutral: "#8a92a3",
  accent: "#f5a623",
};

const ICONS = {
  play: "M8,5.14V19.14L19,12.14L8,5.14Z",
  pause: "M14,19H18V5H14M6,19H10V5H6V19Z",
  stop: "M18,18H6V6H18V18Z",
  plus: "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",
  minus: "M19,13H5V11H19V13Z",
  alert:
    "M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z",
  flame:
    "M17.66,11.2C17.43,10.9 17.15,10.64 16.89,10.38C16.22,9.78 15.46,9.35 14.82,8.72C13.33,7.26 13,4.85 13.95,3C13,3.23 12.17,3.75 11.46,4.32C8.87,6.4 7.85,10.07 9.07,13.22C9.11,13.32 9.15,13.42 9.15,13.55C9.15,13.77 9,13.97 8.8,14.05C8.57,14.15 8.33,14.09 8.14,13.93C8.08,13.88 8.04,13.83 8,13.76C6.87,12.33 6.69,10.28 7.45,8.64C5.78,10 4.87,12.3 5,14.47C5.06,14.97 5.12,15.47 5.29,15.97C5.43,16.57 5.7,17.17 6,17.7C7.08,19.43 8.95,20.67 10.96,20.92C13.1,21.19 15.39,20.8 17.03,19.32C18.86,17.66 19.5,15 18.56,12.72L18.43,12.46C18.22,12 17.66,11.2 17.66,11.2Z",
};

// Temperature steps for the stepper: no heat, then 37 °C (the robot's
// minimum), then every 5 °C up to 120.
const TEMP_STEPS = [0, 37, ...Array.from({ length: 17 }, (_, i) => 40 + i * 5)];
const SPEEDS = Array.from({ length: 11 }, (_, i) => i);
const POWERS = Array.from({ length: 10 }, (_, i) => i + 1);
const TIMER_MAX = 12 * 3600;

// Sections in display order. Each one keeps its own container, so an update
// only touches the parts that changed (the blades keep spinning).
const SECTIONS = ["hero", "banner", "controls", "stats", "setpoints"];

const CONFIRM_MS = 3000;
// A second tap that comes this soon after the first is a double-click, not a
// confirmation.
const CONFIRM_MIN_MS = 400;
// Stepper taps are gathered and sent once the user stops tapping: while the
// robot cooks every change goes to it.
const SEND_DELAY_MS = 700;

// Companion entities by the integration's translation keys.
const KEYS = {
  temperature: ["sensor", "current_temperature"],
  remaining: ["sensor", "remaining_time"],
  error: ["sensor", "error_code"],
  connected: ["binary_sensor", "connected"],
  target_temperature: ["number", "target_temperature"],
  speed: ["number", "speed"],
  power: ["number", "heat_power"],
  timer: ["number", "timer"],
  start: ["button", "start"],
  pause: ["button", "pause"],
  resume: ["button", "resume"],
  stop: ["button", "stop"],
};
// Fallback when the registry has no translation keys: the entity ids that
// Home Assistant builds from the English or Spanish names.
const ID_HINTS = {
  temperature: /_(temperature|temperatura)$/,
  remaining: /_(time_left|tiempo_restante)$/,
  error: /_(error_code|codigo_de_error)$/,
  connected: /_(broker_connection|conexion_al_broker)$/,
  target_temperature: /_(target_temperature|temperatura_objetivo)$/,
  speed: /_(speed|velocidad)$/,
  power: /_(heat_power|potencia_calorifica)$/,
  timer: /_(timer|temporizador)$/,
  start: /_(start|iniciar)$/,
  pause: /_(pause|pausar)$/,
  resume: /_(resume|reanudar)$/,
  stop: /_(stop|parar)$/,
};

function detectLang(hass) {
  const raw =
    (hass && hass.locale && hass.locale.language) ||
    (hass && hass.language) ||
    (typeof navigator !== "undefined" && navigator.language) ||
    "en";
  const lang = String(raw).toLowerCase().replace(/_/g, "-").split("-")[0];
  return Object.prototype.hasOwnProperty.call(STRINGS, lang) ? lang : "en";
}

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

function icon(name, size = 20) {
  return `<svg class="ic" width="${size}" height="${size}" viewBox="0 0 24 24"><path d="${ICONS[name]}"/></svg>`;
}

function num(st) {
  if (!st) return null;
  const v = parseFloat(st.state);
  return isNaN(v) ? null : v;
}

function isUsable(st) {
  return !!st && st.state !== "unavailable" && st.state !== "unknown";
}

// 95 -> "1:35", 3725 -> "1:02:05"
function clock(seconds) {
  if (seconds == null) return "—";
  const s = Math.max(0, Math.round(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const pad = (n) => String(n).padStart(2, "0");
  return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${m}:${pad(s % 60)}`;
}

// The timer stepper moves in steps that fit the time: seconds for short
// timers, minutes for long ones.
function timerStep(value, up) {
  const v = up ? value : value - 1;
  if (v < 60) return 10;
  if (v < 600) return 30;
  if (v < 3600) return 60;
  return 300;
}

function nextTemp(value, up) {
  if (up) return TEMP_STEPS.find((t) => t > value) ?? TEMP_STEPS[TEMP_STEPS.length - 1];
  return [...TEMP_STEPS].reverse().find((t) => t < value) ?? 0;
}

function defaultPower(temp) {
  return temp > 0 ? Math.max(1, Math.min(10, Math.round(temp / 10))) : 0;
}

function deviceName(hass, entityId) {
  const ent = hass.entities && hass.entities[entityId];
  const dev = ent && ent.device_id && hass.devices && hass.devices[ent.device_id];
  return dev ? dev.name_by_user || dev.name || "" : "";
}

// Jar seen from the side: the blades spin while cooking (faster with more
// speed) and steam rises while it heats.
function jarSvg(state, color, speed, heating) {
  const dur = speed > 0 ? (1.4 / Math.sqrt(speed)).toFixed(2) : 0;
  return `
    <svg class="jar ${esc(state)}${heating ? " heating" : ""}" viewBox="0 0 72 72" style="--c:${color};--spin:${dur}s">
      <g class="steam">
        <path d="M28 14c-3-3 3-5 0-8"/>
        <path d="M36 12c-3-3 3-5 0-8"/>
        <path d="M44 14c-3-3 3-5 0-8"/>
      </g>
      <rect class="lid" x="20" y="16" width="32" height="5" rx="2"/>
      <path class="body" d="M21 21h30l-3 36a4 4 0 0 1-4 4H28a4 4 0 0 1-4-4z"/>
      <path class="handle" d="M51 27h5a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3h-6"/>
      <path class="food" d="M23.5 40h25l-1.4 17a2.5 2.5 0 0 1-2.5 2.3H27.4a2.5 2.5 0 0 1-2.5-2.3z"/>
      <g class="blades${speed > 0 && state === "cooking" ? " spinning" : ""}">
        <path d="M27 52h18M36 47v10"/>
      </g>
      <rect class="base" x="18" y="62" width="36" height="6" rx="2"/>
    </svg>`;
}

// Find the integration's other entities on the same device. Only used to
// pre-fill a new card (getStubConfig).
function guessEntities(hass, statusId) {
  const out = {};
  const reg = hass && hass.entities;
  const dev = reg && reg[statusId] && reg[statusId].device_id;
  if (!dev) return out;
  const siblings = Object.values(reg).filter((e) => e.device_id === dev && e.entity_id !== statusId && hass.states[e.entity_id]);
  for (const [key, [domain, tk]] of Object.entries(KEYS)) {
    const inDomain = siblings.filter((e) => e.entity_id.startsWith(domain + "."));
    const hit = inDomain.find((e) => e.translation_key === tk) || inDomain.find((e) => ID_HINTS[key].test(e.entity_id));
    if (hit) out[key] = hit.entity_id;
  }
  return out;
}

function findStatus(hass) {
  const reg = (hass && hass.entities) || {};
  const byKey = Object.values(reg).find((e) => e.platform === "mambo_touch" && e.translation_key === "status");
  if (byKey) return byKey.entity_id;
  return Object.keys((hass && hass.states) || {}).find((id) => /^sensor\.mambo.*_(status|estado)$/.test(id));
}

class MamboHudCardEditor extends HTMLElement {
  _withDefaults(config) {
    return { show_controls: true, show_setpoints: true, ...(config || {}) };
  }
  setConfig(config) {
    this._config = this._withDefaults(config);
    if (this._form) {
      this._form.data = this._config;
      return;
    }
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
    if (this._form && this._builtLang === detectLang(hass)) {
      this._form.hass = hass;
      return;
    }
    this._render();
  }
  connectedCallback() {
    if (!this._form) this._render();
  }
  _schema(E) {
    const ent = (name, label, domain) => ({ name, label, selector: { entity: domain ? { domain } : {} } });
    return [
      {
        type: "expandable", name: "general", title: E.general, flatten: true, expanded: true,
        schema: [
          { ...ent("entity", E.entity, "sensor"), required: true },
          { name: "name", label: E.name, selector: { text: {} } },
        ],
      },
      {
        type: "expandable", name: "status", title: E.status, flatten: true,
        schema: [
          ent("temperature", E.temperature, "sensor"),
          ent("remaining", E.remaining, "sensor"),
          ent("error", E.error, "sensor"),
          ent("connected", E.connected, "binary_sensor"),
        ],
      },
      {
        type: "expandable", name: "setpoints", title: E.setpoints, flatten: true,
        schema: [
          ent("target_temperature", E.targetTemperature, ["number", "input_number"]),
          ent("speed", E.speed, ["number", "input_number"]),
          ent("power", E.power, ["number", "input_number"]),
          ent("timer", E.timer, ["number", "input_number"]),
        ],
      },
      {
        type: "expandable", name: "buttons", title: E.buttons, flatten: true,
        schema: [
          ent("start", E.start, ["button", "script"]),
          ent("pause", E.pause, ["button", "script"]),
          ent("resume", E.resume, ["button", "script"]),
          ent("stop", E.stop, ["button", "script"]),
        ],
      },
      {
        type: "expandable", name: "display", title: E.display, flatten: true,
        schema: [
          { name: "show_controls", label: E.showControls, selector: { boolean: {} } },
          { name: "show_setpoints", label: E.showSetpoints, selector: { boolean: {} } },
        ],
      },
    ];
  }
  _render() {
    if (!this._hass || !this._config) return;
    this._builtLang = detectLang(this._hass);
    this.innerHTML = "";
    const form = document.createElement("ha-form");
    form.hass = this._hass;
    form.data = this._config;
    form.schema = this._schema(STRINGS[this._builtLang].editor);
    form.computeLabel = (s) => s.label || s.title || s.name;
    form.addEventListener("value-changed", (ev) => {
      this._config = ev.detail.value;
      this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
    });
    this._form = form;
    this.appendChild(form);
  }
}
customElements.define("mambo-hud-card-editor", MamboHudCardEditor);

class MamboHudCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("mambo-hud-card-editor");
  }
  static getStubConfig(hass) {
    const entity = findStatus(hass);
    return entity ? { entity, ...guessEntities(hass, entity) } : { entity: "" };
  }
  constructor() {
    super();
    this._pending = {}; // config key -> value shown before it's sent
    this._sendTimers = {};
    this._armedAt = null; // start armed for a confirmation
    this._armTimer = null;
  }
  setConfig(config) {
    if (!config || !config.entity) throw new Error("mambo-hud-card: 'entity' is required");
    this._config = config;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.addEventListener("click", (ev) => this._onClick(ev));
    }
    this._sig = null;
    this._render();
  }
  set hass(hass) {
    this._hass = hass;
    // Only re-render when one of our entities (or the language) changed.
    const sig = this._signature();
    if (sig === this._sig) return;
    this._render();
  }
  getCardSize() {
    return this._config && this._config.show_setpoints === false ? 5 : 9;
  }
  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }
  disconnectedCallback() {
    Object.values(this._sendTimers).forEach(clearTimeout);
    this._sendTimers = {};
    this._pending = {};
    clearTimeout(this._armTimer);
    this._armedAt = null;
  }
  _ids() {
    const c = this._config;
    return ["entity", ...Object.keys(KEYS)].map((k) => c[k]).filter(Boolean);
  }
  _signature() {
    if (!this._hass || !this._config) return null;
    // HA replaces a state object whenever it changes, so comparing
    // last_updated stamps is enough.
    const parts = this._ids().map((id) => {
      const st = this._hass.states[id];
      return st ? st.last_updated + st.state : "-";
    });
    return detectLang(this._hass) + "|" + parts.join("|") + "|" + JSON.stringify(this._pending) + "|" + !!this._armedAt;
  }
  _st(key) {
    const id = this._config[key];
    return id ? this._hass.states[id] : undefined;
  }
  // A set point: what the user just tapped, else the number entity.
  _value(key) {
    if (key in this._pending) return this._pending[key];
    return num(this._st(key));
  }
  _call(domain, service, data) {
    Promise.resolve(this._hass.callService(domain, service, data)).catch((err) =>
      this.dispatchEvent(
        new CustomEvent("hass-notification", { detail: { message: (err && err.message) || String(err) }, bubbles: true, composed: true })
      )
    );
  }
  _press(key) {
    const id = this._config[key];
    if (!id) return;
    const domain = id.split(".")[0];
    this._call(domain, domain === "script" ? "turn_on" : "press", { entity_id: id });
  }
  _moreInfo(entityId) {
    if (!entityId || !this._hass.states[entityId]) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }
  // Show the new value at once and send it when the taps stop.
  _setPoint(key, value) {
    const id = this._config[key];
    if (!id) return;
    this._pending[key] = value;
    if (key === "target_temperature" && this._config.power) this._pending.power = defaultPower(value);
    clearTimeout(this._sendTimers[key]);
    this._sendTimers[key] = setTimeout(() => {
      delete this._sendTimers[key];
      const domain = id.split(".")[0];
      Promise.resolve(this._hass.callService(domain, "set_value", { entity_id: id, value }))
        .catch((err) =>
          this.dispatchEvent(
            new CustomEvent("hass-notification", { detail: { message: (err && err.message) || String(err) }, bubbles: true, composed: true })
          )
        )
        .finally(() => {
          delete this._pending[key];
          if (key === "target_temperature") delete this._pending.power;
          this._render();
        });
    }, SEND_DELAY_MS);
    this._render();
  }
  _onClick(ev) {
    const el = ev.target.closest("[data-action]");
    if (!el || !this._hass || el.disabled) return;
    const { action, value } = el.dataset;
    switch (action) {
      case "more-info":
        this._moreInfo(value);
        break;
      case "start":
        this._start();
        break;
      case "press":
        this._press(value);
        break;
      case "temp": {
        const cur = this._value("target_temperature") ?? 0;
        this._setPoint("target_temperature", nextTemp(cur, value === "up"));
        break;
      }
      case "timer": {
        const cur = this._value("timer") ?? 0;
        const up = value === "up";
        const step = timerStep(cur, up);
        // Land on a multiple of the step, so 0:45 + 10 s reads 0:50.
        const next = up ? Math.floor(cur / step) * step + step : Math.ceil(cur / step) * step - step;
        this._setPoint("timer", Math.max(0, Math.min(TIMER_MAX, next)));
        break;
      }
      case "speed":
        this._setPoint("speed", Number(value));
        break;
      case "power":
        this._setPoint("power", Number(value));
        break;
    }
  }
  // Starting with heat needs two taps: the first arms it for a few seconds
  // and says what it will do, the second starts.
  _start() {
    const temp = this._value("target_temperature") ?? 0;
    if (temp <= 0) {
      this._press("start");
      return;
    }
    if (this._armedAt && Date.now() - this._armedAt < CONFIRM_MIN_MS) return;
    clearTimeout(this._armTimer);
    if (this._armedAt) {
      this._armedAt = null;
      this._press("start");
    } else {
      this._armedAt = Date.now();
      this._armTimer = setTimeout(() => {
        this._armedAt = null;
        this._render();
      }, CONFIRM_MS);
    }
    this._render();
  }
  _stateLabel(st, S) {
    if (!st) return S.labels.notFound;
    if (S.states[st.state]) return S.states[st.state];
    return this._hass.formatEntityState ? this._hass.formatEntityState(st) : st.state;
  }
  _fmt(st) {
    if (!st) return { v: "—", u: "" };
    const v = num(st);
    if (v == null) return { v: "—", u: "" };
    // Home Assistant's own formatting: the entity's decimals and the user's
    // number format (decimal comma).
    if (this._hass.formatEntityStateToParts) {
      const parts = this._hass.formatEntityStateToParts(st);
      const join = (fn) => parts.filter(fn).map((p) => p.value).join("").trim();
      return { v: esc(join((p) => p.type !== "unit")), u: esc(join((p) => p.type === "unit")) };
    }
    return { v: esc(Math.round(v)), u: esc(st.attributes.unit_of_measurement || "") };
  }
  _build() {
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card>
        <div class="title"></div>
        ${SECTIONS.map((k) => `<div class="sec" data-sec="${k}"></div>`).join("")}
      </ha-card>`;
    const root = this.shadowRoot;
    const hero = root.querySelector('[data-sec="hero"]');
    hero.innerHTML = `
      <div class="row hero divider">
        <div class="clickable jar-wrap" data-action="more-info"></div>
        <div class="hero-main clickable" data-action="more-info"></div>
        <div class="clock-slot"></div>
      </div>`;
    this._els = {
      title: root.querySelector(".title"),
      jar: hero.querySelector(".jar-wrap"),
      heroMain: hero.querySelector(".hero-main"),
      clock: hero.querySelector(".clock-slot"),
      sec: {},
    };
    SECTIONS.forEach((k) => (this._els.sec[k] = root.querySelector(`[data-sec="${k}"]`)));
    this._html = new Map();
  }
  // Replace an element's content only when it actually changed.
  _patch(el, html) {
    if (this._html.get(el) === html) return;
    this._html.set(el, html);
    el.innerHTML = html;
  }
  _render() {
    if (!this.shadowRoot || !this._config || !this._hass) return;
    if (!this._els) this._build();
    this._sig = this._signature();
    const S = STRINGS[detectLang(this._hass)];
    const L = S.labels;
    const c = this._config;
    const els = this._els;
    const html = {};

    const status = this._st("entity");
    const state = status ? status.state : "unavailable";
    const attrs = (status && status.attributes) || {};
    const running = state === "cooking" || state === "paused";
    const conn = this._st("connected");
    const offline = (conn && conn.state === "off") || state === "unavailable";

    // While a cook runs show what the robot does; otherwise the set points.
    const target = this._value("target_temperature") ?? 0;
    const speed = this._value("speed") ?? 0;
    const power = this._value("power") ?? 0;
    const timer = this._value("timer") ?? 0;
    const shownTemp = running && attrs.temperature != null ? attrs.temperature : target;
    const shownSpeed = running && attrs.speed != null ? attrs.speed : speed;
    const heating = state === "cooking" && shownTemp > 0;

    let color = COLORS.neutral;
    if (state === "cooking") color = heating ? COLORS.danger : COLORS.low;
    else if (state === "paused") color = COLORS.moderate;

    els.title.textContent = c.name || deviceName(this._hass, c.entity) || attrs.friendly_name || c.entity;

    els.jar.dataset.value = c.entity;
    els.heroMain.dataset.value = c.entity;
    this._patch(els.jar, jarSvg(state, color, shownSpeed, heating));
    const sub = [
      shownTemp > 0 ? `${shownTemp} °C` : L.noHeat,
      `${L.speedShort} ${shownSpeed}`,
      shownTemp > 0 && (running ? attrs.firepower : power) ? `${L.powerShort} ${running ? attrs.firepower : power}` : "",
    ].filter(Boolean);
    this._patch(
      els.heroMain,
      `<div class="hero-state">${esc(this._stateLabel(status, S))}</div><div class="hero-sub">${esc(sub.join(" · "))}</div>`
    );

    // Big clock: time left while cooking, else the timer that will be used.
    const remSt = this._st("remaining");
    const rem = running ? num(remSt) : null;
    const clockKey = running ? "remaining" : "timer";
    this._patch(
      els.clock,
      (running ? rem != null : c.timer)
        ? `<div class="clock clickable" data-action="more-info" data-value="${esc(c[clockKey] || c.entity)}">
            <div class="clock-val" style="color:${running ? color : "inherit"}">${clock(running ? rem : timer)}</div>
            <div class="clock-label">${esc(running ? L.remaining : L.timer)}</div>
          </div>`
        : ""
    );

    // Error / connection banner
    const errSt = this._st("error");
    const errCode = num(errSt);
    html.banner = "";
    if (offline) {
      html.banner = `<div class="banner clickable" data-action="more-info" data-value="${esc(c.connected || c.entity)}">${icon("alert", 18)}<span>${esc(L.offline)}</span></div>`;
    } else if (errCode) {
      html.banner = `<div class="banner clickable" data-action="more-info" data-value="${esc(c.error)}">${icon("alert", 18)}<span>${esc(L.error.replace("{c}", errSt.state))}</span></div>`;
    }

    // Controls
    html.controls = "";
    if (c.show_controls !== false) {
      const btns = [];
      const can = (key) => !!c[key] && !offline;
      if (state === "cooking" && c.pause) btns.push(["press", "pause", "pause", S.actions.pause, true, can("pause")]);
      else if (state === "paused" && c.resume) btns.push(["press", "resume", "play", S.actions.resume, true, can("resume")]);
      else if (c.start) {
        const label = this._armedAt ? S.actions.confirmHeat.replace("{t}", `${target} °C`) : S.actions.start;
        btns.push(["start", "start", "play", label, true, can("start") && timer > 0, this._armedAt ? " armed" : ""]);
      }
      if (c.stop) btns.push(["press", "stop", "stop", S.actions.stop, false, can("stop")]);
      if (btns.length) {
        const hint = !running && c.start && c.timer && timer <= 0 ? `<div class="note center">${esc(L.needsTimer)}</div>` : "";
        html.controls = `<div class="controls-wrap divider"><div class="row controls">${btns
          .map(
            ([action, value, ic, label, primary, enabled, extra = ""]) =>
              `<button class="ctl${primary ? " primary" : ""}${extra}" data-action="${action}" data-value="${value}" title="${esc(label)}"${enabled ? "" : " disabled"}>
                <span class="ctl-ic">${icon(ic, 22)}</span><span class="ctl-label">${esc(label)}</span>
              </button>`
          )
          .join("")}</div>${hint}</div>`;
      }
    }

    // Stats: current temperature, target, time left
    const stat = (key, label, valueHtml) =>
      `<div class="stat clickable" data-action="more-info" data-value="${esc(c[key] || "")}">
        <div class="stat-val">${valueHtml}</div><div class="stat-label">${esc(label)}</div>
      </div>`;
    const stats = [];
    const tempSt = this._st("temperature");
    if (tempSt) {
      const f = this._fmt(tempSt);
      stats.push(stat("temperature", L.temperature, `${f.v}<span class="stat-unit">${f.u}</span>`));
    }
    if (c.target_temperature && running) {
      stats.push(stat("target_temperature", L.target, shownTemp > 0 ? `${shownTemp}<span class="stat-unit">°C</span>` : `<span class="stat-txt">${esc(L.noHeat)}</span>`));
    }
    if (remSt && running) stats.push(stat("remaining", L.remaining, clock(num(remSt))));
    html.stats = stats.length ? `<div class="grid divider">${stats.join("")}</div>` : "";

    // Set points
    html.setpoints = "";
    if (c.show_setpoints !== false) {
      const blocks = [];
      const dis = offline ? " disabled" : "";
      const stepper = (label, action, valueHtml, canDown, canUp, key) =>
        `<div class="sp">
          <div class="section-label">${esc(label)}</div>
          <div class="stepper${key in this._pending ? " pending" : ""}">
            <button class="step" data-action="${action}" data-value="down"${canDown && !offline ? "" : " disabled"}>${icon("minus", 18)}</button>
            <div class="step-val">${valueHtml}</div>
            <button class="step" data-action="${action}" data-value="up"${canUp && !offline ? "" : " disabled"}>${icon("plus", 18)}</button>
          </div>
        </div>`;
      const steppers = [];
      if (c.target_temperature) {
        steppers.push(
          stepper(
            L.temperature, "temp",
            target > 0 ? `${icon("flame", 16)}${target}<span class="stat-unit">°C</span>` : `<span class="stat-txt">${esc(L.noHeat)}</span>`,
            target > 0, target < TEMP_STEPS[TEMP_STEPS.length - 1], "target_temperature"
          )
        );
      }
      if (c.timer) steppers.push(stepper(L.timer, "timer", clock(timer), timer > 0, timer < TIMER_MAX, "timer"));
      if (steppers.length) blocks.push(`<div class="steppers">${steppers.join("")}</div>`);
      const pills = (label, options, current, action, disabled) =>
        `<div class="pills-block">
          <div class="section-label">${esc(label)}</div>
          <div class="pills">${options
            .map((o) => `<button class="pill${o === current ? " on" : ""}" data-action="${action}" data-value="${o}"${disabled ? " disabled" : ""}>${o}</button>`)
            .join("")}</div>
        </div>`;
      if (c.speed) blocks.push(pills(L.speed, SPEEDS, speed, "speed", !!dis));
      if (c.power) {
        blocks.push(
          target > 0
            ? pills(L.power, POWERS, power, "power", !!dis)
            : `<div class="pills-block"><div class="section-label">${esc(L.power)}</div><div class="note">${esc(L.powerNeedsHeat)}</div></div>`
        );
      }
      if (blocks.length) html.setpoints = `<div class="sp-wrap">${blocks.join("")}</div>`;
    }

    SECTIONS.slice(1).forEach((k) => this._patch(els.sec[k], html[k]));
    // No divider under the last section that has something in it.
    const last = [...SECTIONS].reverse().find((k) => k === "hero" || html[k]);
    SECTIONS.forEach((k) => els.sec[k].classList.toggle("last", k === last));
  }
}

const STYLE = `
  :host { display: block; }
  ha-card { display: block; padding: 22px 24px; background: var(--ha-card-background, var(--card-background-color, #fff)); color: var(--primary-text-color, #1c2128); font-family: -apple-system, "Segoe UI", Roboto, sans-serif; overflow: hidden; border-radius: var(--ha-card-border-radius, 12px); box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.12)); border: 1px solid var(--divider-color, rgba(0,0,0,.06)); box-sizing: border-box; height: 100%; }
  [hidden] { display: none !important; }
  .clickable { cursor: pointer; border-radius: 6px; transition: background .15s ease; }
  .clickable:hover { background: rgba(127,127,127,.12); }
  .clickable:active { background: rgba(127,127,127,.18); }
  .title { font-size: 13px; font-weight: 600; color: var(--secondary-text-color, #70788a); margin: 0 0 14px; letter-spacing: .02em; }
  .row { display: flex; }
  .divider { border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08)); }
  .sec.last > .divider { border-bottom: 0; padding-bottom: 0; }
  .ic { fill: currentColor; display: inline-block; vertical-align: middle; flex: none; }
  .section-label { font-size: 9px; letter-spacing: .08em; color: var(--secondary-text-color, #8a92a3); margin-bottom: 7px; text-transform: uppercase; font-weight: 600; }
  .note { font-size: 11.5px; color: var(--secondary-text-color, #70788a); padding: 2px 0; }
  .note.center { text-align: center; padding-top: 10px; }

  .hero { align-items: center; gap: 14px; padding-bottom: 16px; }
  .jar-wrap { flex: none; padding: 2px; }
  .jar { width: 64px; height: 64px; display: block; overflow: visible; }
  .jar .body { fill: var(--card-background-color, #fff); stroke: var(--c); stroke-width: 2.4; stroke-linejoin: round; }
  .jar .handle { fill: none; stroke: var(--c); stroke-width: 2.4; stroke-linecap: round; opacity: .7; }
  .jar .lid { fill: var(--c); opacity: .75; }
  .jar .food { fill: var(--c); opacity: .14; }
  .jar .base { fill: var(--secondary-text-color, #8a92a3); opacity: .45; }
  .jar .blades { stroke: ${COLORS.accent}; stroke-width: 2.2; stroke-linecap: round; transform-box: view-box; transform-origin: 36px 52px; }
  .jar .blades.spinning { animation: spin var(--spin) ease-in-out infinite alternate; }
  .jar .steam path { fill: none; stroke: var(--c); stroke-width: 1.8; stroke-linecap: round; opacity: 0; }
  .jar.heating .steam path { animation: steam 2.4s ease-in-out infinite; }
  .jar.heating .steam path:nth-child(2) { animation-delay: .8s; }
  .jar.heating .steam path:nth-child(3) { animation-delay: 1.6s; }
  @keyframes spin { to { transform: scaleX(-1); } }
  @keyframes steam { 0% { opacity: 0; transform: translateY(4px); } 40% { opacity: .65; } 100% { opacity: 0; transform: translateY(-4px); } }
  @media (prefers-reduced-motion: reduce) { .jar .blades, .jar .steam path { animation: none !important; } }

  .hero-main { flex: 1; min-width: 0; padding: 4px 6px; }
  .hero-state { font-size: 28px; font-weight: 600; line-height: 1.1; }
  .hero-sub { font-size: 12px; color: var(--secondary-text-color, #70788a); margin-top: 5px; }
  .clock-slot { flex: none; }
  .clock { text-align: right; padding: 4px 6px; }
  .clock-val { font-size: 22px; font-weight: 600; font-variant-numeric: tabular-nums; line-height: 1.1; }
  .clock-label { font-size: 9px; color: var(--secondary-text-color, #70788a); margin-top: 3px; }

  .banner { display: flex; align-items: center; gap: 8px; margin-top: 12px; padding: 8px 10px; background: rgba(209,72,28,.1); color: ${COLORS.danger}; font-size: 12px; font-weight: 600; }

  button { font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer; -webkit-tap-highlight-color: transparent; }
  button:disabled { cursor: default; opacity: .35; }
  .controls-wrap { padding: 16px 0; }
  .controls { justify-content: space-around; gap: 8px; }
  .ctl { display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 56px; max-width: 140px; }
  .ctl-ic { width: 46px; height: 46px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid var(--divider-color, rgba(0,0,0,.12)); color: var(--primary-text-color, #1c2128); transition: background .15s ease, transform .1s ease; }
  .ctl:not(:disabled):hover .ctl-ic { background: rgba(127,127,127,.12); }
  .ctl:not(:disabled):active .ctl-ic { transform: scale(.94); }
  .ctl.primary .ctl-ic { background: ${COLORS.low}; border-color: ${COLORS.low}; color: #fff; }
  .ctl.primary:not(:disabled):hover .ctl-ic { background: #24935c; }
  .ctl.armed .ctl-ic { background: ${COLORS.danger}; border-color: ${COLORS.danger}; }
  .ctl.armed .ctl-label { color: ${COLORS.danger}; font-weight: 600; }
  .ctl-label { font-size: 9.5px; color: var(--secondary-text-color, #70788a); text-align: center; line-height: 1.25; }

  .grid { display: flex; flex-wrap: wrap; gap: 18px 28px; padding: 14px 0; }
  .stat { padding: 2px 6px; margin: 0 -6px; }
  .stat-val { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 4px; font-variant-numeric: tabular-nums; }
  .stat-unit { font-size: 12px; color: var(--secondary-text-color, #70788a); font-weight: 400; }
  .stat-txt { font-size: 14px; }
  .stat-label { font-size: 9.5px; color: var(--secondary-text-color, #70788a); margin-top: 2px; }

  .sp-wrap { display: flex; flex-direction: column; gap: 14px; padding-top: 16px; }
  .steppers { display: flex; flex-wrap: wrap; gap: 14px 24px; }
  .sp { flex: 1; min-width: 140px; }
  .stepper { display: flex; align-items: center; gap: 6px; }
  .step { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid var(--divider-color, rgba(0,0,0,.12)); flex: none; transition: background .15s ease; }
  .step:not(:disabled):hover { background: rgba(127,127,127,.12); }
  .step-val { flex: 1; text-align: center; font-size: 18px; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 4px; font-variant-numeric: tabular-nums; }
  .step-val .ic { color: ${COLORS.danger}; }
  .stepper.pending .step-val { color: ${COLORS.info}; }
  /* One row of equal pills: 0-10 fits a phone-width card. */
  .pills { display: flex; gap: 5px; }
  .pill { flex: 1 1 0; min-width: 0; text-align: center; font-size: 11.5px; padding: 5px 0; border-radius: 999px; border: 1px solid var(--divider-color, rgba(0,0,0,.12)); color: var(--secondary-text-color, #70788a); transition: background .15s ease; box-sizing: border-box; }
  .pill:not(:disabled):hover { background: rgba(127,127,127,.12); }
  .pill.on { background: ${COLORS.info}; border-color: ${COLORS.info}; color: #fff; font-weight: 600; }
`;

customElements.define("mambo-hud-card", MamboHudCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "mambo-hud-card",
  name: "Mambo HUD Card",
  description: "Instrument-panel card for the Cecotec Mambo Touch: state, time left, temperature, start / pause / stop, and temperature, speed, heat power and timer",
  preview: true,
  documentationURL: "https://github.com/pablopeza/mambo-hud-card",
});

console.info(`%c MAMBO-HUD-CARD %c v${VERSION} `, "color:#fff;background:#3b82c4;font-weight:600", "color:#3b82c4");
