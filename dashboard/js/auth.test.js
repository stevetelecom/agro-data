/**
 * Rôle : tests de la connexion (cas normal et cas invalide).
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import assert from "node:assert/strict";
import test from "node:test";
import { getSession, isSessionExpired, login, logout, togglePasswordState, validateLogin } from "./auth.js";

/**
 * Remplace le stockage de session, absent hors navigateur.
 */
function installSessionStorage() {
  const store = new Map();
  globalThis.sessionStorage = {
    getItem(key) {
      return store.has(key) ? store.get(key) : null;
    },
    setItem(key, value) {
      store.set(key, String(value));
    },
    removeItem(key) {
      store.delete(key);
    },
  };
}

test("accepte un e-mail et un mot de passe d'au moins 8 caractères", () => {
  assert.equal(validateLogin("acheteur@agrodata.local", "Acheteur2026!"), null);
});

test("refuse une saisie vide", () => {
  assert.match(validateLogin("  ", ""), /e-mail et le mot de passe/);
});

test("refuse un e-mail mal formé", () => {
  assert.match(validateLogin("pas-un-email", "Acheteur2026!"), /e-mail valide/);
});

test("refuse un mot de passe trop court", () => {
  assert.match(validateLogin("acheteur@agrodata.local", "court"), /8 caractères/);
});

test("affiche puis masque le mot de passe", () => {
  const shown = togglePasswordState(false);
  assert.equal(shown.type, "text");
  assert.equal(shown.icon, "visibility_off");
  assert.equal(shown.label, "Masquer le mot de passe");

  const hidden = togglePasswordState(true);
  assert.equal(hidden.type, "password");
  assert.equal(hidden.icon, "visibility");
  assert.equal(hidden.label, "Afficher le mot de passe");
});

test("ouvre une session de démonstration quand l'API est injoignable", async () => {
  installSessionStorage();
  globalThis.fetch = async () => {
    throw new Error("offline");
  };
  await login("admin@agrodata.local", "Admin2026!");
  const session = getSession();
  assert.equal(session.email, "admin@agrodata.local");
  assert.equal(session.role, "admin");
  assert.equal(session.mode, "demo");
  logout();
  assert.equal(getSession(), null);
});

function bearer(payload) {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `eyJhbGciOiJIUzI1NiJ9.${body}.signature`;
}

test("enregistre le jeton de l'API dans la session, sans le mot de passe", async () => {
  installSessionStorage();
  const exp = Math.floor(Date.now() / 1000) + 3600;
  const token = bearer({ sub: "lecteur@agro-data.local", role: "acheteur", exp });
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({ access_token: token, token_type: "bearer" }),
  });
  await login("lecteur@agro-data.local", "ChangeMe123!");
  const session = getSession();
  assert.equal(session.mode, "api");
  assert.equal(session.role, "acheteur");
  assert.equal(session.email, "lecteur@agro-data.local");
  assert.equal(session.token, token);
  assert.equal(session.expiresAt, exp);
  assert.equal(session.password, undefined);
  logout();
});

test("ne bascule pas en démonstration quand l'API refuse les identifiants", async () => {
  installSessionStorage();
  globalThis.fetch = async () => ({
    ok: false,
    status: 401,
    json: async () => ({ detail: "Identifiants invalides" }),
  });
  await assert.rejects(
    () => login("acheteur@agrodata.local", "Acheteur2026!"),
    /Identifiants invalides/,
  );
  assert.equal(getSession(), null);
});

test("efface une session dont le jeton a expiré", () => {
  installSessionStorage();
  const expired = {
    email: "lecteur@agro-data.local",
    role: "acheteur",
    token: "expired",
    mode: "api",
    expiresAt: Math.floor(Date.now() / 1000) - 30,
  };
  assert.equal(isSessionExpired(expired), true);
  sessionStorage.setItem("agro_session", JSON.stringify(expired));
  assert.equal(getSession(), null);
  assert.equal(sessionStorage.getItem("agro_session"), null);
});

test("annonce un service indisponible quand l'API est injoignable et le compte inconnu", async () => {
  installSessionStorage();
  globalThis.fetch = async () => {
    throw new TypeError("fetch failed");
  };
  await assert.rejects(
    () => login("admin@agrodata.local", "Mauvais2026!"),
    /indisponible/,
  );
  assert.equal(getSession(), null);
});

test("ne bascule pas en démonstration quand l'API répond une erreur 500", async () => {
  installSessionStorage();
  globalThis.fetch = async () => ({
    ok: false,
    status: 500,
    json: async () => ({ detail: "Erreur interne" }),
  });
  await assert.rejects(
    () => login("admin@agrodata.local", "Admin2026!"),
    /HTTP 500/,
  );
  assert.equal(getSession(), null);
});
