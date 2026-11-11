/**
 * Rôle : lecture du fichier .env à la racine du dépôt.
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

export async function apiBase() {
  const env = await loadEnv();
  const value = String(env.API_BASE_URL || "http://127.0.0.1:8000").trim().replace(/\/$/, "");
  if (!/^https?:\/\/\S+$/.test(value)) return "http://127.0.0.1:8000";
  return value;
}
