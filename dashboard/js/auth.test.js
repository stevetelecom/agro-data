/**
 * Rôle : tests de la connexion (cas normal et cas invalide).
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import assert from "node:assert/strict";
import test from "node:test";
import { getSession, login, logout, togglePasswordState, validateLogin } from "./auth.js";

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

test("refuse des identifiants de démonstration incorrects", async () => {
  installSessionStorage();
  globalThis.fetch = async () => {
    throw new Error("offline");
  };
  await assert.rejects(
    () => login("admin@agrodata.local", "Mauvais2026!"),
    /Identifiants refusés/,
  );
  assert.equal(getSession(), null);
});
