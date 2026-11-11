/**
 * Rôle : tests du passage des mesures API vers le graphique et le tableau.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import assert from "node:assert/strict";
import test from "node:test";
import { adaptApiWorkspace } from "./api.js";
import { buildForecast, seriesByHour } from "./metrics.js";

test("relie une mesure API à la parcelle et à la série d'humidité", () => {
  const workspace = adaptApiWorkspace({
    plots: [{ id: 1, code: "P-NORD", name: "Parcelle Nord", location_label: "Ambam Nord" }],
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
  assert.equal(workspace.measurements[0].climate.air_humidity_pct, 88.2);
  const series = seriesByHour(workspace.measurements, workspace.plots);
  assert.equal(series.length, 1);
  assert.equal(series[0].humidity, 88.2);
  assert.equal(typeof series[0].index, "number");
  const forecast = buildForecast(series[0].index, false);
  assert.equal(forecast.length, 7);
  assert.ok(forecast.every((point) => point.priceFcfaKg > 0));
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
