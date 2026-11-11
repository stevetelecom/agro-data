/**
 * Rôle : tests de validation des formulaires de gestion (cas normal et cas invalide).
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3)
 */

import assert from "node:assert/strict";
import test from "node:test";
import { validateDevice, validatePlot, validateSubscriber } from "./api.js";

const db = {
  plots: [{ id: "1", code: "P-NORD", name: "Parcelle Nord" }],
  devices: [{ id: "4", device_id: "AMB-P001", plot_id: "1" }],
  subscribers: [{ id: "8", email: "export@yaounde.cm" }],
};

test("accepte une parcelle, un appareil et un abonné valides", () => {
  const plot = validatePlot({ code: "p-est", name: "Parcelle Est", location_label: "Ambam Est" }, db, null);
  assert.deepEqual(plot.errors, {});
  assert.equal(plot.value.code, "P-EST");

  const device = validateDevice({
    device_id: "amb-p004",
    label: "Boîtier Est",
    plot_id: "1",
    status: "actif",
  }, db, null);
  assert.deepEqual(device.errors, {});
  assert.equal(device.value.device_id, "AMB-P004");

  const subscriber = validateSubscriber({
    organization: "Export SA",
    email: "Nouveau@Yaounde.cm",
    plan: "Marché",
  }, db, null);
  assert.deepEqual(subscriber.errors, {});
  assert.equal(subscriber.value.email, "nouveau@yaounde.cm");
});

test("refuse un code, un appareil et un e-mail invalides", () => {
  const plot = validatePlot({ code: "P", name: "A", location_label: "" }, db, null);
  assert.match(plot.errors.code, /2 à 32/);
  assert.match(plot.errors.name, /2 caractères/);
  assert.match(plot.errors.location_label, /secteur/);

  const duplicate = validatePlot({ code: "P-NORD", name: "Autre", location_label: "Ambam" }, db, null);
  assert.match(duplicate.errors.code, /déjà utilisé/);

  const device = validateDevice({ device_id: "BOITE", label: "X", plot_id: "9", status: "" }, db, null);
  assert.match(device.errors.device_id, /AMB-P/);
  assert.match(device.errors.label, /libellé/);
  assert.match(device.errors.plot_id, /parcelle/);
  assert.match(device.errors.status, /statut/);

  const subscriber = validateSubscriber({ organization: "E", email: "pas-un-email", plan: "" }, db, null);
  assert.match(subscriber.errors.organization, /organisation/);
  assert.match(subscriber.errors.email, /e-mail valide/);
  assert.match(subscriber.errors.plan, /formule/);
});
