# ChargeWindow for Home Assistant

Home Assistant custom integration **and** a branded Lovelace card for
[ChargeWindow](https://chargewindow.eu) — price-optimized EV charging.

The integration polls a public, anonymous ChargeWindow endpoint and exposes the
current electricity price, the cheapest upcoming charging window, projected
savings, grid CO2 intensity, and an hourly price series you can plot with the
included custom card.

> **Status:** release (`0.2.0`). The card now ships *inside* the integration and
> is auto-registered — a single HACS install of the integration delivers the
> card too, with no manual dashboard-resource step. The Python and JS are
> written to the documented backend contract; end-to-end validation against a
> live Home Assistant instance is the next step.

---

## What you get

### Sensors (grouped under one device, "ChargeWindow (&lt;area&gt;)")

| Entity | Description |
| --- | --- |
| `sensor.chargewindow_current_price` | All-in current price (`<currency>/kWh`). **Carries the full `hours` series in its attributes** — this is the entity the card reads. |
| `sensor.chargewindow_spot_price` | Spot-only current price. |
| `sensor.chargewindow_cheapest_window_start` | Start of the cheapest window (timestamp). |
| `sensor.chargewindow_cheapest_window_end` | End of the cheapest window (timestamp). |
| `sensor.chargewindow_cheapest_window_avg_price` | Average price across the cheapest window. |
| `sensor.chargewindow_savings_vs_now` | Absolute savings vs charging now (attribute: `percent`). |
| `sensor.chargewindow_co2_intensity` | Current grid CO2 intensity (`gCO2/kWh`), `unavailable` when the backend has no value. |
| `binary_sensor.chargewindow_is_cheap_now` | `on` when charging right now is currently considered cheap. |

All entities degrade gracefully to `unknown` / `unavailable` when a field is
missing and never crash the update coordinator.

### Backend endpoint

The integration polls this public, anonymous endpoint:

```
GET {base_url}/api/integrations/homeassistant/state?area=DK2&currency=DKK
```

Production `base_url` is `https://chargewindow.eu`. Supported areas:
`DK1`, `DK2`, `SE1`–`SE4`, `NO1`–`NO5`.

---

## Installation

### 1. Integration (custom component)

**Manual (recommended for now):**

1. Copy the `custom_components/chargewindow` folder into your Home Assistant
   `config/custom_components/` directory so you have
   `config/custom_components/chargewindow/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**, search for
   **ChargeWindow**, and follow the setup flow.

**Via HACS (custom repository):**

1. HACS → **Integrations** → three-dot menu → **Custom repositories**.
2. Add `https://github.com/Munkeholm/chargewindow-homeassistant` with category
   **Integration**.
3. Install **ChargeWindow**, then restart Home Assistant and add the
   integration as above.

### 2. Custom Lovelace card — no extra step

The card is **bundled with the integration** and **auto-registered**. When the
integration is installed and set up, it serves the card over HTTP and loads it
into the frontend for you (served at `/chargewindow/chargewindow-card.js`,
cache-busted by the integration version).

**You do NOT need to add a dashboard resource.** Just [add the card to a
dashboard](#adding-the-card-to-a-dashboard) once at least one config entry is
set up. (If the card type isn't recognized right after first setup, reload the
dashboard / clear the browser cache.)

---

## Configuration

Setup is entirely UI-driven (config flow). You provide:

- **Base URL** — default `https://chargewindow.eu`
- **Area** — dropdown of supported bidding zones, default `DK2`
- **Currency** — default `DKK`
- **Update interval (minutes)** — default `5` (changeable later via the
  integration's **Configure** / options)

Setup makes one test call to the endpoint and shows a friendly error if it
fails. Each `(base_url, area)` pair is a unique entry, so you can track multiple
zones side by side.

---

## Adding the card to a dashboard

The card module is auto-registered by the integration, so you can add a manual
card directly (no Resources entry needed):

```yaml
type: custom:chargewindow-card
entity: sensor.chargewindow_current_price
title: ChargeWindow
```

The card renders a calculator-style bar graph of the hourly price series:

- **Past** hours are muted,
- **upcoming** hours use the accent color,
- the **cheapest window** hours are green (ChargeWindow green `#1fbf4b`),
- a dashed **"now"** marker sits at the past/upcoming boundary,
- the header shows the current price, the cheapest window (start–end), and the
  "−X% vs charging now" savings figure.

The card is dependency-free vanilla JS, responsive, and reads everything from
the single `current_price` sensor's attributes (falling back to companion
sensors for the header where available).

---

## Example automations

### 1. Notify when charging becomes cheap

```yaml
alias: Notify when charging is cheap
trigger:
  - platform: state
    entity_id: binary_sensor.chargewindow_is_cheap_now
    to: "on"
action:
  - service: notify.notify
    data:
      title: ChargeWindow
      message: >
        Electricity is cheap right now
        ({{ states('sensor.chargewindow_current_price') }}
        {{ state_attr('sensor.chargewindow_current_price', 'currency') }}/kWh).
        Good time to charge.
mode: single
```

### 2. Charge the wallbox during the cheapest window

Turns a wallbox switch on at the start of the cheapest window and off at the
end. Replace `switch.wallbox` with your actual entity.

```yaml
alias: Charge EV during cheapest window
trigger:
  - platform: template
    value_template: >
      {{ now() >= as_datetime(states('sensor.chargewindow_cheapest_window_start'))
         and now() < as_datetime(states('sensor.chargewindow_cheapest_window_end')) }}
    id: window_on
  - platform: template
    value_template: >
      {{ now() >= as_datetime(states('sensor.chargewindow_cheapest_window_end')) }}
    id: window_off
condition:
  - condition: template
    value_template: >
      {{ states('sensor.chargewindow_cheapest_window_start') not in
         ['unknown', 'unavailable', 'none'] }}
action:
  - choose:
      - conditions:
          - condition: trigger
            id: window_on
        sequence:
          - service: switch.turn_on
            target:
              entity_id: switch.wallbox
      - conditions:
          - condition: trigger
            id: window_off
        sequence:
          - service: switch.turn_off
            target:
              entity_id: switch.wallbox
mode: single
```

---

## Development notes

- No extra pip requirements — the integration uses Home Assistant's bundled
  `aiohttp` via `async_get_clientsession`, all I/O is async.
- CI (`.github/workflows/validate.yml`) runs Home Assistant **hassfest** and the
  **HACS** validation action (category `integration`).

## License

See repository. Keep any secrets (tokens, personal URLs) out of committed YAML.
