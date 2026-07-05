/**
 * ChargeWindow Lovelace card
 *
 * A dependency-free custom element that renders a calculator-style
 * electricity-price bar graph from the ChargeWindow current-price sensor.
 *
 * Config:
 *   type: custom:chargewindow-card
 *   entity: sensor.chargewindow_dk2_current_price   # carries the `hours` attribute
 *   title: ChargeWindow                             # optional
 *
 * The sensor's attributes are expected to contain:
 *   area, currency, generated_at_utc, is_cheap_now,
 *   savings_vs_now_percent, savings_vs_now_absolute, co2_intensity,
 *   cheapest_window_start, cheapest_window_end, cheapest_window_avg_price,
 *   hours: [ { hourLocal, priceAllIn, isPast, isCheap }, ... ]
 *
 * Everything the card needs is read from this ONE entity.
 */

const CW_VERSION = "0.3.0";
const CW_GREEN = "#1fbf4b";

class ChargeWindowCard extends HTMLElement {
  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("You must define an 'entity' (the ChargeWindow current price sensor).");
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("hui-generic-entity-row");
  }

  /**
   * Auto-select the correct entity when the user first adds the card.
   * Prefers an area-suffixed id (e.g. sensor.chargewindow_dk2_current_price),
   * falling back to the plain sensor.chargewindow_current_price.
   */
  static getStubConfig(hass) {
    let entity = "sensor.chargewindow_current_price";
    if (hass && hass.states) {
      const re = /^sensor\.chargewindow_.*_current_price$/;
      const match = Object.keys(hass.states).find((id) => re.test(id));
      if (match) {
        entity = match;
      } else if (hass.states["sensor.chargewindow_current_price"]) {
        entity = "sensor.chargewindow_current_price";
      }
    }
    return { entity, title: "ChargeWindow" };
  }

  _fmt(value, digits = 2) {
    if (value === null || value === undefined || isNaN(Number(value))) return "–";
    return Number(value).toFixed(digits);
  }

  _isNum(value) {
    return value !== null && value !== undefined && !isNaN(Number(value));
  }

  _fmtTime(iso) {
    if (!iso) return "–";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  _fmtHour(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    const hh = String(d.getHours()).padStart(2, "0");
    return `${hh}:00`;
  }

  _shell(inner) {
    return `
      <ha-card header="${this._escape(this._config.title || "ChargeWindow")}">
        <div class="cw-body">${inner}</div>
      </ha-card>
      ${this._style()}
    `;
  }

  _escape(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  _render() {
    if (!this._hass || !this._config) return;

    const entityId = this._config.entity;
    const stateObj = this._hass.states[entityId];

    if (!stateObj) {
      this.innerHTML = this._shell(
        `<div class="cw-msg">Entity <code>${this._escape(entityId)}</code> not found. Waiting for data…</div>`
      );
      return;
    }

    const attrs = stateObj.attributes || {};
    const hours = Array.isArray(attrs.hours) ? attrs.hours : [];
    const currency = attrs.currency || "";
    const unit = attrs.unit_of_measurement || (currency ? `${currency}/kWh` : "");

    if (hours.length === 0) {
      this.innerHTML = this._shell(
        `<div class="cw-msg">Waiting for hourly price data…</div>`
      );
      return;
    }

    // Everything the header needs now lives on the current_price entity.
    const currentPrice = stateObj.state;
    const savingsPercent = attrs.savings_vs_now_percent;
    const savingsAbsolute = attrs.savings_vs_now_absolute;
    const windowStart = attrs.cheapest_window_start;
    const windowEnd = attrs.cheapest_window_end;
    const windowAvg = attrs.cheapest_window_avg_price;
    const co2 = attrs.co2_intensity;

    const hasSavings = this._isNum(savingsPercent);
    const savingsBlock = hasSavings
      ? `
        <div class="cw-metric cw-savings">
          <div class="cw-metric-label">vs charging now</div>
          <div class="cw-metric-value cw-savings-value">&minus;${this._fmt(
            Math.abs(Number(savingsPercent)),
            0
          )}%</div>
          ${
            this._isNum(savingsAbsolute)
              ? `<div class="cw-metric-sub">${this._fmt(
                  Math.abs(Number(savingsAbsolute))
                )} ${this._escape(unit)}</div>`
              : ""
          }
        </div>`
      : "";

    const windowAvgSub = this._isNum(windowAvg)
      ? `<div class="cw-metric-sub">avg ${this._fmt(windowAvg)} ${this._escape(unit)}</div>`
      : "";

    const co2Chip = this._isNum(co2)
      ? `<div class="cw-co2-chip" title="Current grid CO₂ intensity">${this._fmt(
          co2,
          0
        )} gCO₂/kWh</div>`
      : "";

    const header = `
      <div class="cw-header">
        <div class="cw-metric">
          <div class="cw-metric-label">Now</div>
          <div class="cw-metric-value">${this._fmt(currentPrice)} <span class="cw-unit">${this._escape(unit)}</span></div>
        </div>
        <div class="cw-metric">
          <div class="cw-metric-label">Cheapest window</div>
          <div class="cw-metric-value">${this._fmtTime(windowStart)}&ndash;${this._fmtTime(windowEnd)}</div>
          ${windowAvgSub}
        </div>
        ${savingsBlock}
      </div>
      ${co2Chip}
    `;

    this.innerHTML = this._shell(header + `<div class="cw-chart"></div>`);
    this._drawChart(hours, unit);
  }

  _drawChart(hours, unit) {
    const container = this.querySelector(".cw-chart");
    if (!container) return;

    const prices = hours.map((h) => Number(h.priceAllIn)).filter((p) => !isNaN(p));
    if (prices.length === 0) {
      container.innerHTML = `<div class="cw-msg">No valid prices to plot.</div>`;
      return;
    }
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(0, Math.min(...prices));

    // Layout in a responsive viewBox; the SVG scales to the card width.
    const W = 700;
    const H = 220;
    const padL = 8;
    const padR = 8;
    const padT = 10;
    const padB = 34;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;
    const n = hours.length;
    const gap = 2;
    const barW = Math.max(1, plotW / n - gap);

    const scaleY = (p) => {
      const range = maxPrice - minPrice || 1;
      return plotH - ((p - minPrice) / range) * plotH;
    };

    let firstUpcomingIndex = hours.findIndex((h) => !h.isPast);
    if (firstUpcomingIndex < 0) firstUpcomingIndex = n;

    let bars = "";
    hours.forEach((h, i) => {
      const price = Number(h.priceAllIn);
      const x = padL + i * (plotW / n) + gap / 2;
      const y = padT + scaleY(isNaN(price) ? minPrice : price);
      const hgt = Math.max(1, padT + plotH - y);
      let cls = "cw-bar-upcoming";
      if (h.isCheap) cls = "cw-bar-cheap";
      else if (h.isPast) cls = "cw-bar-past";
      // Hover tooltip: HH:00, price, and past / cheapest-window status.
      let note = "";
      if (h.isCheap) note = " · cheapest window";
      else if (h.isPast) note = " · past";
      const label = `${this._fmtHour(h.hourLocal)} — ${this._fmt(price)} ${unit}${note}`;
      bars += `<rect class="${cls}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${hgt.toFixed(1)}" rx="1.5"><title>${this._escape(label)}</title></rect>`;
    });

    // "Now" marker at the past/upcoming boundary.
    let nowMarker = "";
    if (firstUpcomingIndex > 0 && firstUpcomingIndex < n) {
      const nx = padL + firstUpcomingIndex * (plotW / n);
      nowMarker = `
        <line class="cw-now-line" x1="${nx.toFixed(1)}" y1="${padT}" x2="${nx.toFixed(1)}" y2="${padT + plotH}" />
        <text class="cw-now-label" x="${(nx + 3).toFixed(1)}" y="${padT + 12}">now</text>
      `;
    }

    // Hour ticks (every ~4 hours) for orientation.
    let ticks = "";
    const tickEvery = Math.max(1, Math.round(n / 8));
    hours.forEach((h, i) => {
      if (i % tickEvery !== 0) return;
      const x = padL + i * (plotW / n) + (plotW / n) / 2;
      ticks += `<text class="cw-tick" x="${x.toFixed(1)}" y="${H - 12}" text-anchor="middle">${this._fmtTime(h.hourLocal)}</text>`;
    });

    container.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" class="cw-svg" role="img" aria-label="Hourly electricity prices">
        ${bars}
        ${nowMarker}
        ${ticks}
      </svg>
      <div class="cw-legend">
        <span><i class="dot past"></i>Past</span>
        <span><i class="dot upcoming"></i>Upcoming</span>
        <span><i class="dot cheap"></i>Cheapest window</span>
      </div>
    `;
  }

  _style() {
    return `
      <style>
        ha-card { overflow: hidden; }
        .cw-body { padding: 0 16px 16px; }
        .cw-msg { padding: 24px 0; color: var(--secondary-text-color); }
        .cw-msg code { font-family: monospace; }
        .cw-header {
          display: flex; flex-wrap: wrap; gap: 16px;
          padding: 4px 0 10px;
        }
        .cw-metric { flex: 1 1 30%; min-width: 90px; }
        .cw-metric-label {
          font-size: 0.72rem; text-transform: uppercase;
          letter-spacing: 0.04em; color: var(--secondary-text-color);
        }
        .cw-metric-value {
          font-size: 1.35rem; font-weight: 600;
          color: var(--primary-text-color);
        }
        .cw-metric-sub {
          font-size: 0.78rem; color: var(--secondary-text-color); margin-top: 1px;
        }
        .cw-unit { font-size: 0.8rem; font-weight: 400; color: var(--secondary-text-color); }
        .cw-savings-value { color: ${CW_GREEN}; }
        .cw-co2-chip {
          display: inline-block; margin: 0 0 12px;
          padding: 3px 10px; border-radius: 999px;
          font-size: 0.75rem; font-weight: 500;
          color: var(--secondary-text-color);
          background: color-mix(in srgb, var(--secondary-text-color) 14%, transparent);
          border: 1px solid var(--divider-color);
        }
        .cw-chart { width: 100%; }
        .cw-svg { width: 100%; height: 220px; display: block; }
        /* PAST: muted, low emphasis — reads in both light & dark. */
        .cw-bar-past { fill: var(--disabled-text-color, #9e9e9e); opacity: 0.35; }
        /* UPCOMING: neutral mid emphasis via secondary text color. */
        .cw-bar-upcoming { fill: var(--secondary-text-color, #6b7280); opacity: 0.55; }
        /* CHEAPEST WINDOW: bold brand green = "charge here". */
        .cw-bar-cheap { fill: ${CW_GREEN}; opacity: 1; }
        .cw-now-line {
          stroke: var(--primary-text-color); stroke-width: 1.5;
          stroke-dasharray: 3 3; opacity: 0.7;
        }
        .cw-now-label {
          fill: var(--primary-text-color); font-size: 11px; opacity: 0.8;
        }
        .cw-tick { fill: var(--secondary-text-color); font-size: 10px; }
        .cw-legend {
          display: flex; gap: 16px; flex-wrap: wrap;
          margin-top: 6px; font-size: 0.75rem; color: var(--secondary-text-color);
        }
        .cw-legend .dot {
          display: inline-block; width: 10px; height: 10px;
          border-radius: 2px; margin-right: 5px; vertical-align: middle;
        }
        .cw-legend .dot.past { background: var(--disabled-text-color, #9e9e9e); opacity: 0.5; }
        .cw-legend .dot.upcoming { background: var(--secondary-text-color, #6b7280); opacity: 0.55; }
        .cw-legend .dot.cheap { background: ${CW_GREEN}; }
      </style>
    `;
  }
}

// Idempotent registration: safe even if the module is loaded more than once
// (e.g. bundled auto-register via add_extra_js_url AND a manual resource).
if (!customElements.get("chargewindow-card")) {
  customElements.define("chargewindow-card", ChargeWindowCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c && c.type === "chargewindow-card")) {
  window.customCards.push({
    type: "chargewindow-card",
    name: "ChargeWindow Card",
    description: "Calculator-style electricity price bar graph for ChargeWindow.",
    preview: false,
  });
}

// eslint-disable-next-line no-console
console.info(
  `%c CHARGEWINDOW-CARD %c ${CW_VERSION} `,
  `background:${CW_GREEN};color:#fff;font-weight:700;border-radius:3px 0 0 3px;padding:2px 4px;`,
  "background:#222;color:#fff;border-radius:0 3px 3px 0;padding:2px 4px;"
);
