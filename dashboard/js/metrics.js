/**
 * Rôle : règles métier RM1, RM2 et RM3 affichées par le dashboard.
 *        Ces calculs ne servent qu'en mode démonstration, sans backend :
 *        connecté à l'API, le dashboard affiche /api/v1/kpis et
 *        /api/v1/prices/forecast. Les constantes et la formule RM3 sont donc
 *        identiques à backend/app/services/pricing.py, pour que les deux
 *        sources ne divergent jamais.
 * Auteur : NEGOUE Patrick
 * Bloc : B
 */

export const HUMIDITY_ALERT = 85;
export const ALERT_HOURS = 48;
// Alignés sur pricing.py : 1050 FCFA/kg et k = 0,15 (formule v1).
export const PRICE_REFERENCE_FCFA_KG = 1050;
export const PRICE_COEFFICIENT = 0.15;
export const PRICE_FORMULA_VERSION = "v1";
export const INDEX_FORMULA_VERSION = "RM2-v1";

export function consecutiveHoursAbove(measurements, threshold = HUMIDITY_ALERT) {
  const sorted = [...measurements].sort((a, b) => a.timestamp - b.timestamp);
  let streak = 0;
  for (let index = sorted.length - 1; index >= 0; index -= 1) {
    const point = sorted[index];
    if (index < sorted.length - 1) {
      const gapHours = (sorted[index + 1].timestamp - point.timestamp) / 3600;
      if (gapHours > 1.5) break;
    }
    if (Number(point.climate?.air_humidity_pct) > threshold) streak += 1;
    else break;
  }
  return streak;
}

export function detectionRate(measurements) {
  if (measurements.length === 0) return 0;
  const hits = measurements.filter((item) => Number(item.diagnostic_ia?.phytophthora_detected) === 1).length;
  return hits / measurements.length;
}

export function infestationIndex(hoursAbove, rate) {
  const climatePart = 60 * Math.min(1, hoursAbove / ALERT_HOURS);
  const visionPart = 40 * Math.min(1, Math.max(0, rate));
  return Math.round((climatePart + visionPart) * 10) / 10;
}

export function levelFromIndex(index) {
  if (index < 30) return "faible";
  if (index <= 60) return "modere";
  return "eleve";
}

export function priceFromIndex(index) {
  // prix = référence x (1 + k x indice / 100), comme adjust_price() côté API.
  return Math.round(PRICE_REFERENCE_FCFA_KG * (1 + (PRICE_COEFFICIENT * index) / 100));
}

export function averageHumidity(measurements, windowHours = 24) {
  if (measurements.length === 0) return null;
  const latest = Math.max(...measurements.map((item) => item.timestamp));
  const windowed = measurements.filter((item) => item.timestamp >= latest - windowHours * 3600);
  const sample = windowed.length > 0 ? windowed : measurements;
  const sum = sample.reduce((total, item) => total + Number(item.climate.air_humidity_pct), 0);
  return Math.round((sum / sample.length) * 10) / 10;
}

export function summarize(measurements, plots) {
  const perPlot = plots.map((plot) => {
    const series = measurements.filter((item) => item.device_id === plot.device_id);
    const hours = consecutiveHoursAbove(series);
    const rate = detectionRate(series);
    const index = series.length === 0 ? 0 : infestationIndex(hours, rate);
    const referenceKg = Number(plot.reference_volume_kg) || 0;
    return {
      ...plot,
      samples: series.length,
      hours,
      rate,
      index,
      level: levelFromIndex(index),
      humidity: averageHumidity(series),
      alert: hours > ALERT_HOURS,
      referenceKg,
      healthyKg: Math.round(referenceKg * (1 - index / 100)),
    };
  });

  const withData = perPlot.filter((plot) => plot.samples > 0);
  const base = withData.length > 0 ? withData : perPlot;
  const mean = (values) => values.reduce((total, value) => total + value, 0) / values.length;
  const humidityValues = base.map((plot) => plot.humidity).filter((value) => value !== null);
  const index = base.length ? Math.round(mean(base.map((plot) => plot.index)) * 10) / 10 : 0;

  return {
    plots: perPlot,
    global: {
      index,
      level: levelFromIndex(index),
      humidity: humidityValues.length ? Math.round(mean(humidityValues) * 10) / 10 : null,
      alerts: perPlot.filter((plot) => plot.alert).length,
      healthyKg: perPlot.reduce((total, plot) => total + plot.healthyKg, 0),
    },
  };
}

export function seriesByHour(measurements, plots) {
  const stamps = [...new Set(measurements.map((item) => item.timestamp))].sort((a, b) => a - b);
  return stamps.map((timestamp) => {
    const humidities = [];
    const indexes = [];
    plots.forEach((plot) => {
      const history = measurements
        .filter((item) => item.device_id === plot.device_id && item.timestamp <= timestamp)
        .sort((a, b) => a.timestamp - b.timestamp);
      if (history.length === 0) return;
      const current = history[history.length - 1];
      if (current.timestamp === timestamp) humidities.push(Number(current.climate.air_humidity_pct));
      indexes.push(infestationIndex(consecutiveHoursAbove(history), detectionRate(history)));
    });
    const mean = (values) => values.reduce((total, value) => total + value, 0) / values.length;
    return {
      timestamp,
      humidity: humidities.length ? Math.round(mean(humidities) * 10) / 10 : null,
      index: indexes.length ? Math.round(mean(indexes) * 10) / 10 : null,
    };
  });
}

export function buildForecast(globalIndex, alertActive) {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const points = [];
  for (let day = 0; day < 7; day += 1) {
    const drift = alertActive ? day * 1.6 : 0;
    const index = Math.round(Math.min(100, globalIndex + drift) * 10) / 10;
    const date = new Date(start.getTime() + day * 86400000);
    points.push({
      date: date.toISOString().slice(0, 10),
      index,
      priceFcfaKg: priceFromIndex(index),
      reference: PRICE_REFERENCE_FCFA_KG,
      coefficient: PRICE_COEFFICIENT,
      formula: PRICE_FORMULA_VERSION,
    });
  }
  return points;
}
