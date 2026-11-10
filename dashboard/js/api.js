/**
 * Rôle : appels REST du bloc B, avec repli sur le jeu local
 *        quand l'API FastAPI ne répond pas.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import { getSession } from "./auth.js";
import { loadDemoDb, resetDemoDb, saveDemoDb } from "./demo-data.js";
import { apiBase } from "./env.js";

export { resetDemoDb };

export class ApiError extends Error {
  constructor(message, errors = null) {
    super(message);
    this.errors = errors;
  }
}

function clean(value, max) {
  return String(value ?? "").replace(/[\u0000-\u001F\u007F]/g, "").trim().slice(0, max);
}

function unwrap(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

function normalizeMeasurement(raw) {
  return {
    id: String(raw.id ?? `${raw.device_id}-${raw.timestamp}`),
    device_id: String(raw.device_id ?? ""),
    timestamp: Number(raw.timestamp),
    climate: {
      temperature_c: Number(raw.climate?.temperature_c),
      air_humidity_pct: Number(raw.climate?.air_humidity_pct),
      soil_humidity_pct: Number(raw.climate?.soil_humidity_pct),
    },
    diagnostic_ia: {
      phytophthora_detected: Number(raw.diagnostic_ia?.phytophthora_detected) === 1 ? 1 : 0,
      confidence: Number(raw.diagnostic_ia?.confidence ?? 0),
    },
    geo_enc: raw.geo_enc ?? "",
  };
}

function isDemo() {
  return getSession()?.mode !== "api";
}

async function request(path, options = {}) {
  const session = getSession();
  const headers = { Accept: "application/json" };
  if (options.body) headers["Content-Type"] = "application/json";
  if (session?.token && session.mode === "api") headers.Authorization = `Bearer ${session.token}`;
  let response;
  try {
    response = await fetch(`${await apiBase()}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(4000),
    });
  } catch {
    throw new ApiError("Le service est momentanément indisponible.");
  }
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(payload?.message || "La requête a été refusée.", payload?.errors || null);
  }
  return payload;
}

export async function loadWorkspace() {
  if (isDemo()) return loadDemoDb();
  const [plots, devices, subscribers, measurements] = await Promise.all([
    request("/api/v1/plots"),
    request("/api/v1/devices"),
    request("/api/v1/subscribers"),
    request("/api/v1/measurements"),
  ]);
  return {
    version: 1,
    plots: unwrap(plots),
    devices: unwrap(devices),
    subscribers: unwrap(subscribers),
    measurements: unwrap(measurements)
      .map(normalizeMeasurement)
      .filter((item) => item.device_id && Number.isFinite(item.timestamp)),
  };
}

function validatePlot(input, db, currentId) {
  const errors = {};
  const name = clean(input.name, 80);
  const sector = clean(input.sector, 80);
  const deviceId = clean(input.device_id, 20).toUpperCase();
  const volume = Number(String(input.reference_volume_kg ?? "").replace(",", "."));
  if (name.length < 2) errors.name = "Indiquez un nom d'au moins 2 caractères.";
  if (sector.length < 2) errors.sector = "Indiquez le secteur de la parcelle.";
  if (!/^AMB-P\d{3}$/.test(deviceId)) {
    errors.device_id = "Format attendu : AMB-P suivi de 3 chiffres, par exemple AMB-P004.";
  } else if (db.plots.some((plot) => plot.device_id === deviceId && plot.id !== currentId)) {
    errors.device_id = "Cet identifiant est déjà utilisé par une autre parcelle.";
  }
  if (!Number.isFinite(volume) || volume < 0 || volume > 100000) {
    errors.reference_volume_kg = "Indiquez un volume entre 0 et 100 000 kg.";
  }
  return {
    errors,
    value: { name, sector, device_id: deviceId, reference_volume_kg: Math.round(volume) },
  };
}

function validateDevice(input, db, currentId) {
  const errors = {};
  const deviceId = clean(input.device_id, 20).toUpperCase();
  const plotId = clean(input.plot_id, 80);
  const status = input.status === "hors_ligne" || input.status === "actif" ? input.status : "";
  if (!/^AMB-P\d{3}$/.test(deviceId)) {
    errors.device_id = "Format attendu : AMB-P suivi de 3 chiffres.";
  } else if (db.devices.some((device) => device.device_id === deviceId && device.id !== currentId)) {
    errors.device_id = "Cet appareil existe déjà.";
  }
  if (!db.plots.some((plot) => plot.id === plotId)) errors.plot_id = "Choisissez une parcelle.";
  if (!status) errors.status = "Choisissez un statut.";
  return { errors, value: { device_id: deviceId, plot_id: plotId, status } };
}

function validateSubscriber(input, db, currentId) {
  const errors = {};
  const name = clean(input.name, 80);
  const email = clean(input.email, 120).toLowerCase();
  const role = input.role === "admin" || input.role === "acheteur" ? input.role : "";
  const plan = ["Exploitation", "Marché", "Lecture"].includes(input.plan) ? input.plan : "";
  if (name.length < 2) errors.name = "Indiquez un nom d'au moins 2 caractères.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Indiquez un e-mail valide.";
  else if (db.subscribers.some((item) => item.email === email && item.id !== currentId)) {
    errors.email = "Cet e-mail est déjà utilisé.";
  }
  if (!role) errors.role = "Choisissez un rôle.";
  if (!plan) errors.plan = "Choisissez une formule.";
  return { errors, value: { name, email, role, plan } };
}

function rejectIfInvalid(result) {
  if (Object.keys(result.errors).length > 0) {
    throw new ApiError("Vérifiez le formulaire.", result.errors);
  }
  return result.value;
}

async function mutateDemo(mutator) {
  const db = loadDemoDb();
  mutator(db);
  saveDemoDb(db);
}

export async function createPlot(input) {
  if (!isDemo()) return request("/api/v1/plots", { method: "POST", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validatePlot(input, db, null));
    db.plots.push({ id: crypto.randomUUID(), ...value });
  });
  return null;
}

export async function updatePlot(id, input) {
  if (!isDemo()) return request(`/api/v1/plots/${encodeURIComponent(id)}`, { method: "PUT", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validatePlot(input, db, id));
    const plot = db.plots.find((item) => item.id === id);
    if (!plot) throw new ApiError("Parcelle introuvable.");
    Object.assign(plot, value);
  });
  return null;
}

export async function deletePlot(id) {
  if (!isDemo()) return request(`/api/v1/plots/${encodeURIComponent(id)}`, { method: "DELETE" });
  await mutateDemo((db) => {
    const plot = db.plots.find((item) => item.id === id);
    db.plots = db.plots.filter((item) => item.id !== id);
    if (!plot) return;
    db.devices = db.devices.filter((device) => device.plot_id !== id && device.device_id !== plot.device_id);
    db.measurements = db.measurements.filter((item) => item.device_id !== plot.device_id);
  });
}

export async function createDevice(input) {
  if (!isDemo()) return request("/api/v1/devices", { method: "POST", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validateDevice(input, db, null));
    db.devices.push({ id: crypto.randomUUID(), ...value });
  });
  return null;
}

export async function updateDevice(id, input) {
  if (!isDemo()) return request(`/api/v1/devices/${encodeURIComponent(id)}`, { method: "PUT", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validateDevice(input, db, id));
    const device = db.devices.find((item) => item.id === id);
    if (!device) throw new ApiError("Appareil introuvable.");
    Object.assign(device, value);
  });
  return null;
}

export async function deleteDevice(id) {
  if (!isDemo()) return request(`/api/v1/devices/${encodeURIComponent(id)}`, { method: "DELETE" });
  await mutateDemo((db) => {
    db.devices = db.devices.filter((item) => item.id !== id);
  });
}

export async function createSubscriber(input) {
  if (!isDemo()) return request("/api/v1/subscribers", { method: "POST", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validateSubscriber(input, db, null));
    db.subscribers.push({ id: crypto.randomUUID(), ...value });
  });
  return null;
}

export async function updateSubscriber(id, input) {
  if (!isDemo()) return request(`/api/v1/subscribers/${encodeURIComponent(id)}`, { method: "PUT", body: input });
  await mutateDemo((db) => {
    const value = rejectIfInvalid(validateSubscriber(input, db, id));
    const subscriber = db.subscribers.find((item) => item.id === id);
    if (!subscriber) throw new ApiError("Abonné introuvable.");
    Object.assign(subscriber, value);
  });
  return null;
}

export async function deleteSubscriber(id) {
  if (!isDemo()) return request(`/api/v1/subscribers/${encodeURIComponent(id)}`, { method: "DELETE" });
  await mutateDemo((db) => {
    db.subscribers = db.subscribers.filter((item) => item.id !== id);
  });
}
