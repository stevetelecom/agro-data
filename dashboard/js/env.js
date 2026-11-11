/**
 * Rôle : adresse de base de l'API.
 *        Priorité : window.AGRO_CONFIG (dashboard/config.js) ou
 *        window.AGRO_API_BASE, puis le fichier .env de la racine s'il est
 *        servi, puis http://127.0.0.1:8000.
 * Auteur : NEGOUE Patrick
 * Bloc : B
 */

let pending = null;

function parseEnv(text) {
  const env = {};
  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) return;
    const separator = trimmed.indexOf("=");
    if (separator === -1) return;
    const key = trimmed.slice(0, separator).trim();
    let value = trimmed.slice(separator + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    env[key] = value;
  });
  return env;
}

export function loadEnv() {
  if (!pending) {
    pending = fetch(new URL("../../.env", import.meta.url), { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("Fichier .env introuvable.");
        return response.text();
      })
      .then(parseEnv)
      .catch(() => ({}));
  }
  return pending;
}

/** Normalise une adresse d'API ; renvoie null si elle est inutilisable. */
export function normalizeApiBase(value) {
  const trimmed = String(value ?? "").trim().replace(/\/$/, "");
  return /^https?:\/\/\S+$/.test(trimmed) ? trimmed : null;
}

/** Adresse configurée dans le navigateur (dashboard/config.js), si présente. */
function browserConfig() {
  if (typeof window === "undefined") return null;
  return window.AGRO_CONFIG?.apiBaseUrl ?? window.AGRO_API_BASE ?? null;
}

export async function apiBase() {
  const configured = normalizeApiBase(browserConfig());
  if (configured) return configured;
  const env = await loadEnv();
  return normalizeApiBase(env.API_BASE_URL) ?? "http://127.0.0.1:8000";
}
