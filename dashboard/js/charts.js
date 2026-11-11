/**
 * Rôle : graphiques d'humidité, d'indice et de prix prédictif.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3)
 */

import { formatDateTime, formatNumber } from "./format.js";
import { HUMIDITY_ALERT } from "./metrics.js";

let charts = [];

/** Détruit les graphiques Chart.js encore affichés. */
export function destroyCharts() {
  charts.splice(0).forEach((chart) => chart.destroy());
}

function reducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* Chart.js ne résout pas les variables CSS : on lit les jetons calculés, comme
   la maquette qui trace ses SVG avec var(--brun), var(--or) et var(--ko). */
function cssVar(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function baseOptions(yTitle) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: reducedMotion() ? false : { duration: 450 },
    plugins: {
      legend: { position: "bottom", labels: { boxWidth: 12, usePointStyle: true } },
      tooltip: { mode: "index", intersect: false },
    },
    scales: {
      x: { ticks: { maxTicksLimit: 6 }, grid: { display: false } },
      y: { title: { display: true, text: yTitle }, grid: { color: cssVar("--chart-grid", "rgba(43, 26, 18, 0.07)") } },
    },
  };
}

/**
 * Trace l'humidité, l'indice d'infestation et le prix prévisionnel.
 * @returns {boolean} faux s'il n'y a aucune série à afficher
 */
export function renderCharts({ humidityCanvas, indexCanvas, priceCanvas, series, forecast }) {
  destroyCharts();
  if (!window.Chart || series.length === 0) return false;
  window.Chart.defaults.font.family = "Poppins, sans-serif";
  window.Chart.defaults.color = cssVar("--muted", "#7a5c48");
  const labels = series.map((point) => formatDateTime(point.timestamp));
  charts.push(new window.Chart(humidityCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Humidité de l'air",
          data: series.map((point) => point.humidity),
          borderColor: cssVar("--chart-humidity", "#8b4a2b"),
          backgroundColor: cssVar("--chart-humidity-fill", "rgba(139, 74, 43, 0.12)"),
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: "Seuil 85 %",
          data: series.map(() => HUMIDITY_ALERT),
          borderColor: cssVar("--chart-threshold", "#a63d2f"),
          borderDash: [5, 5],
          pointRadius: 0,
          borderWidth: 1.5,
        },
      ],
    },
    options: baseOptions("%"),
  }));
  charts.push(new window.Chart(indexCanvas, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Indice d'infestation",
        data: series.map((point) => point.index),
        borderColor: cssVar("--chart-index", "#c8873a"),
        backgroundColor: cssVar("--chart-index-fill", "rgba(200, 135, 58, 0.14)"),
        fill: true,
        tension: 0.25,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: {
      ...baseOptions("Indice"),
      scales: {
        ...baseOptions("Indice").scales,
        y: { ...baseOptions("Indice").scales.y, suggestedMin: 0, suggestedMax: 100 },
      },
    },
  }));
  charts.push(new window.Chart(priceCanvas, {
    type: "line",
    data: {
      labels: forecast.map((point) => point.date),
      datasets: [{
        label: "Prix indicatif (FCFA/kg)",
        data: forecast.map((point) => point.priceFcfaKg),
        borderColor: cssVar("--chart-price", "#5a3020"),
        backgroundColor: cssVar("--chart-price-fill", "rgba(90, 48, 32, 0.1)"),
        fill: true,
        tension: 0.2,
        pointRadius: 3,
        borderWidth: 2,
      }],
    },
    options: baseOptions("FCFA/kg"),
  }));
  humidityCanvas.setAttribute("aria-label", `Humidité, dernier point ${formatNumber(series.at(-1)?.humidity)} %`);
  return true;
}
