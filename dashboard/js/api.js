/**
 * Rôle : appels REST du bloc B, avec repli sur le jeu local
 *        quand l'API FastAPI ne répond pas.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import { getSession, logout } from "./auth.js";
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

function apiMessage(payload, fallback) {
  if (typeof payload?.detail === "string" && payload.detail) return payload.detail;
  if (typeof payload?.message === "string" && payload.message) return payload.message;
  return fallback;
}

/**
 * Aligne une mesure API (champs à plat ou contrat JSON) sur le modèle du dashboard.
 * @param {object} raw
 */
export function normalizeMeasurement(raw) {
  const climate = raw.climate || {};
  const diagnostic = raw.diagnostic_ia || {};
  return {
    id: String(raw.id ?? `${raw.device_id}-${raw.timestamp}`),
    device_id: String(raw.device_id ?? ""),
    timestamp: Number(raw.timestamp),
    climate: {
      temperature_c: Number(climate.temperature_c ?? raw.temperature_c),
      air_humidity_pct: Number(climate.air_humidity_pct ?? raw.air_humidity_pct),
      soil_humidity_pct: Number(climate.soil_humidity_pct ?? raw.soil_humidity_pct),
    },
    diagnostic_ia: {
      phytophthora_detected: Number(diagnostic.phytophthora_detected ?? raw.phytophthora_detected) === 1 ? 1 : 0,
      confidence: Number(diagnostic.confidence ?? raw.confidence ?? 0),
    },
    geo_enc: raw.geo_enc ?? "",
  };
}

/**
 * Relie les listes REST au modèle utilisé par les graphiques et le tableau.
 * @param {{plots?: object[], devices?: object[], subscribers?: object[], measurements?: object[]}} payload
 */
export function adaptApiWorkspace(payload) {
  const devices = (payload.devices || []).map((raw) => ({
    id: String(raw.id),
    device_id: String(raw.device_id ?? ""),
    label: raw.label || "",
    plot_id: raw.plot_id == null ? "" : String(raw.plot_id),
    status: raw.status || (raw.is_active === false ? "hors_ligne" : "actif"),
  }));
  const plots = (payload.plots || []).map((raw) => {
    const id = String(raw.id);
    const linked = devices.find((device) => device.plot_id === id);
    return {
      id,
      code: raw.code || "",
      name: raw.name || raw.code || "Parcelle",
      sector: raw.sector || raw.location_label || "",
      device_id: raw.device_id || linked?.device_id || "",
      reference_volume_kg: Number(raw.reference_volume_kg ?? 0),
    };
  });
  const subscribers = (payload.subscribers || []).map((raw) => ({
    id: String(raw.id),
    name: raw.name || raw.organization || raw.email || "Abonné",
    email: raw.email || "",
    role: raw.role === "admin" ? "admin" : "acheteur",
    plan: raw.plan || "Lecture",
  }));
  const measurements = (payload.measurements || [])
    .map(normalizeMeasurement)
    .filter((item) => item.device_id && Number.isFinite(item.timestamp));
  return { version: 1, plots, devices, subscribers, measurements };
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
  if (response.status === 401) {
    logout();
    if (typeof location !== "undefined") location.replace("index.html");
    throw new ApiError("La session a expiré. Reconnectez-vous.");
  }
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(apiMessage(payload, "La requête a été refusée."), fieldErrors(payload));
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
  return adaptApiWorkspace({
    plots: unwrap(plots),
    devices: unwrap(devices),
    subscribers: unwrap(subscribers),
    measurements: unwrap(measurements),
  });
}

function fieldErrors(payload) {
  const errors = {};
  if (Array.isArray(payload?.detail)) {
    payload.detail.forEach((item) => {
      const loc = Array.isArray(item.loc) ? item.loc : [];
      const field = loc[loc.length - 1];
      if (typeof field === "string" && field !== "body") errors[field] = item.msg || "Valeur refusée.";
    });
  } else if (typeof payload?.detail === "string") {
    if (/device/i.test(payload.detail)) errors.device_id = payload.detail;
    else if (/e-?mail|abonné/i.test(payload.detail)) errors.email = payload.detail;
    else if (/parcelle introuvable/i.test(payload.detail)) errors.plot_id = payload.detail;
    else if (/code|parcelle/i.test(payload.detail)) errors.code = payload.detail;
  }
  if (payload?.errors && typeof payload.errors === "object") Object.assign(errors, payload.errors);
  return Object.keys(errors).length > 0 ? errors : null;
}

/**
 * Contrôle une parcelle avant envoi.
 * @param {object} input
 * @param {{plots?: object[]}} db
 * @param {string | null} currentId
 * @returns {{errors: object, value: {code: string, name: string, location_label: string}}}
 */
export function validatePlot(input, db, currentId) {
  const errors = {};
  const code = clean(input.code, 64).toUpperCase();
  const name = clean(input.name, 255);
  const location = clean(input.location_label ?? input.sector, 255);
  if (!/^[A-Z0-9][A-Z0-9-]{1,31}$/.test(code)) {
    errors.code = "Code de 2 à 32 caractères : lettres, chiffres et tirets.";
  } else if ((db?.plots || []).some((plot) => plot.code === code && plot.id !== currentId)) {
    errors.code = "Ce code est déjà utilisé.";
  }
  if (name.length < 2) errors.name = "Indiquez un nom d'au moins 2 caractères.";
  if (location.length < 2) errors.location_label = "Indiquez le secteur de la parcelle.";
  return { errors, value: { code, name, location_label: location } };
}

/**
 * Contrôle un appareil avant envoi.
 * @param {object} input
 * @param {{plots?: object[], devices?: object[]}} db
 * @param {string | null} currentId
 */
export function validateDevice(input, db, currentId) {
  const errors = {};
  const deviceId = clean(input.device_id, 64).toUpperCase();
  const label = clean(input.label, 255);
  const plotId = clean(input.plot_id, 80);
  const status = input.status === "hors_ligne" || input.status === "actif" ? input.status : "";
  if (!/^AMB-P\d{3}$/.test(deviceId)) {
    errors.device_id = "Format attendu : AMB-P suivi de 3 chiffres.";
  } else if ((db?.devices || []).some((device) => device.device_id === deviceId && device.id !== currentId)) {
    errors.device_id = "Cet appareil existe déjà.";
  }
  if (label.length < 2) errors.label = "Indiquez un libellé d'au moins 2 caractères.";
  if (!(db?.plots || []).some((plot) => plot.id === plotId)) errors.plot_id = "Choisissez une parcelle.";
  if (!status) errors.status = "Choisissez un statut.";
  return { errors, value: { device_id: deviceId, label, plot_id: plotId, status } };
}

/**
 * Contrôle un abonné avant envoi.
 * @param {object} input
 * @param {{subscribers?: object[]}} db
 * @param {string | null} currentId
 */
export function validateSubscriber(input, db, currentId) {
  const errors = {};
  const organization = clean(input.organization ?? input.name, 255);
  const email = clean(input.email, 255).toLowerCase();
  const plan = clean(input.plan, 64);
  if (organization.length < 2) errors.organization = "Indiquez une organisation d'au moins 2 caractères.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = "Indiquez un e-mail valide.";
  else if ((db?.subscribers || []).some((item) => item.email === email && item.id !== currentId)) {
    errors.email = "Cet e-mail est déjà utilisé.";
  }
  if (plan.length < 2) errors.plan = "Indiquez une formule.";
  return { errors, value: { organization, email, plan } };
}

function toPlotBody(value, update) {
  const body = { name: value.name, location_label: value.location_label };
  if (!update) body.code = value.code;
  return body;
}

function toDeviceBody(value) {
  const plotId = Number(value.plot_id);
  return {
    device_id: value.device_id,
    label: value.label,
    plot_id: Number.isInteger(plotId) ? plotId : null,
    is_active: value.status === "actif",
  };
}

function toSubscriberBody(value, update) {
  const body = { organization: value.organization, plan: value.plan, is_active: true };
  if (!update) body.email = value.email;
  return body;
}

function rememberPlot(value, id) {
  return {
    id,
    code: value.code,
    name: value.name,
    sector: value.location_label,
    device_id: "",
    reference_volume_kg: 0,
  };
}

function rememberDevice(value, id) {
  return { id, ...value };
}

function rememberSubscriber(value, id) {
  return { id, name: value.organization, email: value.email, role: "acheteur", plan: value.plan };
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

/**
 * Crée une parcelle après validation. `db` sert au contrôle d'unicité.
 * @param {object} input
 * @param {{plots?: object[]}} db
 */
export async function createPlot(input, db) {
  const value = rejectIfInvalid(validatePlot(input, db, null));
  if (!isDemo()) return request("/api/v1/plots", { method: "POST", body: toPlotBody(value, false) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validatePlot(input, live, null));
    live.plots.push(rememberPlot(stored, crypto.randomUUID()));
  });
  return null;
}

/**
 * Met à jour une parcelle après validation.
 * @param {string} id
 * @param {object} input
 * @param {{plots?: object[]}} db
 */
export async function updatePlot(id, input, db) {
  const value = rejectIfInvalid(validatePlot(input, db, id));
  if (!isDemo()) return request(`/api/v1/plots/${encodeURIComponent(id)}`, { method: "PUT", body: toPlotBody(value, true) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validatePlot(input, live, id));
    const plot = live.plots.find((item) => item.id === id);
    if (!plot) throw new ApiError("Parcelle introuvable.");
    Object.assign(plot, rememberPlot(stored, id));
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

/**
 * Crée un appareil après validation.
 * @param {object} input
 * @param {{plots?: object[], devices?: object[]}} db
 */
export async function createDevice(input, db) {
  const value = rejectIfInvalid(validateDevice(input, db, null));
  if (!isDemo()) return request("/api/v1/devices", { method: "POST", body: toDeviceBody(value) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validateDevice(input, live, null));
    live.devices.push(rememberDevice(stored, crypto.randomUUID()));
  });
  return null;
}

/**
 * Met à jour un appareil après validation.
 * @param {string} id
 * @param {object} input
 * @param {{plots?: object[], devices?: object[]}} db
 */
export async function updateDevice(id, input, db) {
  const value = rejectIfInvalid(validateDevice(input, db, id));
  if (!isDemo()) return request(`/api/v1/devices/${encodeURIComponent(id)}`, { method: "PUT", body: toDeviceBody(value) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validateDevice(input, live, id));
    const device = live.devices.find((item) => item.id === id);
    if (!device) throw new ApiError("Appareil introuvable.");
    Object.assign(device, rememberDevice(stored, id));
  });
  return null;
}

export async function deleteDevice(id) {
  if (!isDemo()) return request(`/api/v1/devices/${encodeURIComponent(id)}`, { method: "DELETE" });
  await mutateDemo((db) => {
    db.devices = db.devices.filter((item) => item.id !== id);
  });
}

/**
 * Crée un abonné après validation.
 * @param {object} input
 * @param {{subscribers?: object[]}} db
 */
export async function createSubscriber(input, db) {
  const value = rejectIfInvalid(validateSubscriber(input, db, null));
  if (!isDemo()) return request("/api/v1/subscribers", { method: "POST", body: toSubscriberBody(value, false) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validateSubscriber(input, live, null));
    live.subscribers.push(rememberSubscriber(stored, crypto.randomUUID()));
  });
  return null;
}

/**
 * Met à jour un abonné après validation.
 * @param {string} id
 * @param {object} input
 * @param {{subscribers?: object[]}} db
 */
export async function updateSubscriber(id, input, db) {
  const value = rejectIfInvalid(validateSubscriber(input, db, id));
  if (!isDemo()) return request(`/api/v1/subscribers/${encodeURIComponent(id)}`, { method: "PUT", body: toSubscriberBody(value, true) });
  await mutateDemo((live) => {
    const stored = rejectIfInvalid(validateSubscriber(input, live, id));
    const subscriber = live.subscribers.find((item) => item.id === id);
    if (!subscriber) throw new ApiError("Abonné introuvable.");
    Object.assign(subscriber, rememberSubscriber(stored, id));
  });
  return null;
}

export async function deleteSubscriber(id) {
  if (!isDemo()) return request(`/api/v1/subscribers/${encodeURIComponent(id)}`, { method: "DELETE" });
  await mutateDemo((db) => {
    db.subscribers = db.subscribers.filter((item) => item.id !== id);
  });
}
