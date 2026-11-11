/**
 * Rôle : tests du passage des mesures API vers le graphique et le tableau.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import assert from "node:assert/strict";
import test from "node:test";
import { adaptApiWorkspace, adaptPriceForecast } from "./api.js";
import { buildForecast, priceFromIndex, seriesByHour } from "./metrics.js";

test("relie une mesure API à la parcelle et à la série d'humidité", () => {
  const workspace = adaptApiWorkspace({
    plots: [{
      id: 1,
      code: "P-NORD",
      name: "Parcelle Nord",
      location_label: "Ambam Nord",
      village: "Ambam",
      surface_ha: 1.5,
      reference_volume_kg: 1200,
    }],
    devices: [{ id: 4, device_id: "AMB-P001", label: "Boîtier Nord", plot_id: 1, is_active: true }],
    subscribers: [],
    measurements: [{
      id: 9,
      device_id: "AMB-P001",
      timestamp: 1731225600,
      temperature_c: 27.4,
      air_humidity_pct: 88.2,
      soil_humidity_pct: 61,
      phytophthora_detected: 0,
      confidence: 0.93,
      geo_enc: "",
    }],
  });
  assert.equal(workspace.plots[0].device_id, "AMB-P001");
  assert.equal(workspace.plots[0].village, "Ambam");
  assert.equal(workspace.plots[0].reference_volume_kg, 1200);
  assert.equal(workspace.measurements[0].climate.air_humidity_pct, 88.2);
  const series = seriesByHour(workspace.measurements, workspace.plots);
  assert.equal(series.length, 1);
  assert.equal(series[0].humidity, 88.2);
  assert.equal(typeof series[0].index, "number");
  const forecast = buildForecast(series[0].index, false);
  assert.equal(forecast.length, 7);
  assert.ok(forecast.every((point) => point.priceFcfaKg > 0));
});

test("le prix local suit la formule v1 de l'API (1050 FCFA/kg, k = 0,15)", () => {
  // API : 1050 x (1 + 0,15 x 60 / 100) = 1144,5 FCFA/kg.
  assert.ok(Math.abs(priceFromIndex(60) - 1144.5) <= 0.5);
  assert.equal(priceFromIndex(0), 1050);
  const forecast = buildForecast(60, false);
  assert.equal(forecast[0].reference, 1050);
  assert.equal(forecast[0].formula, "v1");
});

test("adapte la courbe de prix du contrat §4.5", () => {
  const forecast = adaptPriceForecast({
    unit: "FCFA/kg",
    horizon_days: 2,
    is_demo: true,
    formula_version: "v1",
    points: [
      { date: "2026-11-09", reference_price: 1050, adjusted_price: 1050 },
      { date: "2026-11-10", reference_price: 1050, adjusted_price: 1147.65 },
    ],
  });
  assert.equal(forecast.formulaVersion, "v1");
  assert.equal(forecast.points[1].priceFcfaKg, 1147.65);
  assert.equal(forecast.points[1].reference, 1050);
});

test("écarte une mesure API incomplète", () => {
  const workspace = adaptApiWorkspace({
    plots: [],
    devices: [],
    subscribers: [],
    measurements: [{ id: 1, timestamp: 10, air_humidity_pct: 50 }],
  });
  assert.equal(workspace.measurements.length, 0);
  assert.equal(seriesByHour(workspace.measurements, workspace.plots).length, 0);
});
