/**
 * Rôle : session, bascule d'affichage du mot de passe, écran de connexion.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B4)
 */

import { apiBase } from "./env.js";
import { showToast } from "./toast.js";

const SESSION_KEY = "agro_session";
const PASSWORD_MIN_LENGTH = 8;

// Comptes de secours hors ligne, alignés sur le contrat §4.8 et sur la
// maquette : ce sont les mêmes identifiants que l'API. Ils n'ouvrent qu'une
// session locale de démonstration, sans jeton serveur.
const DEMO_USERS = [
  { email: "acheteur@ebolowa.cm", password: "demo1234", name: "Acheteur Ebolowa", role: "admin" },
  { email: "lecteur@ebolowa.cm", password: "demo1234", name: "Lecteur Ebolowa", role: "acheteur" },
];

/**
 * Lit la charge utile d'un JWT sans vérifier la signature.
 * La signature est contrôlée par l'API à chaque requête.
 * @param {string} token
 * @returns {{sub?: string, role?: string, exp?: number} | null}
 */
export function readTokenClaims(token) {
  try {
    const part = String(token ?? "").split(".")[1];
    if (!part) return null;
    const padded = part.replace(/-/g, "+").replace(/_/g, "/");
    const json = atob(padded.padEnd(Math.ceil(padded.length / 4) * 4, "="));
    const claims = JSON.parse(json);
    return claims && typeof claims === "object" ? claims : null;
  } catch {
    return null;
  }
}

/**
 * Indique si un jeton d'API a dépassé sa date d'expiration.
 * @param {{mode?: string, expiresAt?: number} | null} session
 * @param {number} nowMs
 */
export function isSessionExpired(session, nowMs = Date.now()) {
  if (!session || session.mode !== "api" || !session.expiresAt) return false;
  return nowMs >= Number(session.expiresAt) * 1000;
}

/**
 * Lit la session courante. Une session API expirée est effacée.
 * @returns {{email: string, name: string, role: string, token: string, mode: string, expiresAt: number | null} | null}
 */
export function getSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw);
    if (isSessionExpired(session)) {
      sessionStorage.removeItem(SESSION_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

/**
 * Efface la session locale.
 */
export function logout() {
  sessionStorage.removeItem(SESSION_KEY);
}

/**
 * Enregistre la session après une connexion acceptée.
 * @param {{email: string, name: string, role: string, token: string, mode: string}} session
 */
function saveSession(session) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

/**
 * Contrôle les champs du formulaire avant tout appel réseau.
 * Le mot de passe doit contenir au moins 8 caractères.
 * @param {string} email
 * @param {string} password
 * @returns {string | null} message d'erreur, ou null si la saisie est acceptable
 */
export function validateLogin(email, password) {
  const identity = String(email ?? "").trim();
  const secret = String(password ?? "");
  if (!identity || !secret) return "Indiquez l'e-mail et le mot de passe.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(identity)) return "Indiquez un e-mail valide.";
  if (secret.length < PASSWORD_MIN_LENGTH) return "Le mot de passe doit contenir au moins 8 caractères.";
  return null;
}

/**
 * Décrit l'état du champ après un clic sur l'icône afficher / masquer.
 * @param {boolean} showing vrai si le mot de passe est déjà visible
 * @returns {{type: string, pressed: string, label: string, icon: string}}
 */
export function togglePasswordState(showing) {
  if (showing) {
    return {
      type: "password",
      pressed: "false",
      label: "Afficher le mot de passe",
      icon: "visibility",
    };
  }
  return {
    type: "text",
    pressed: "true",
    label: "Masquer le mot de passe",
    icon: "visibility_off",
  };
}

/**
 * Ouvre une session via l'API, ou via les comptes de démonstration si l'API ne répond pas.
 * @param {string} email
 * @param {string} password
 */
export async function login(email, password) {
  const problem = validateLogin(email, password);
  if (problem) throw new Error(problem);

  const identity = String(email ?? "").trim().toLowerCase();
  const secret = String(password ?? "");

  // Le repli sur les comptes de démonstration n'est autorisé que si l'API est
  // réellement injoignable (réseau, timeout). Un refus du serveur (401, 403,
  // 422, 429, 5xx) ne doit jamais devenir une session de démonstration :
  // l'utilisateur verrait « identifiants refusés » alors que le service est en
  // cause, ou entrerait dans le dashboard sans le savoir.
  let apiUnreachable = false;
  try {
    const response = await fetch(`${await apiBase()}/api/v1/auth/login`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ email: identity, password: secret }),
      signal: AbortSignal.timeout(8000),
    });
    if (response.status === 401 || response.status === 403 || response.status === 422) {
      const payload = await response.json().catch(() => ({}));
      const detail = typeof payload.detail === "string" ? payload.detail : payload.message;
      const rejected = new Error(detail || "Identifiants refusés.");
      rejected.loginRejected = true;
      throw rejected;
    }
    if (response.ok) {
      const payload = await response.json();
      const token = payload.access_token || payload.token;
      if (!token) {
        const rejected = new Error("La connexion n'a pas abouti. Réessayez.");
        rejected.loginRejected = true;
        throw rejected;
      }
      const claims = readTokenClaims(token) || {};
      const email = String(claims.sub || identity);
      saveSession({
        email,
        name: email,
        role: claims.role === "admin" ? "admin" : "acheteur",
        token,
        mode: "api",
        expiresAt: Number(claims.exp) || null,
      });
      return;
    }
    const refused = new Error(
      `Le service a refusé la connexion (HTTP ${response.status}). Réessayez dans un instant.`,
    );
    refused.serviceResponse = true;
    throw refused;
  } catch (error) {
    // Toute erreur qui ne vient pas d'une réponse HTTP (réseau, timeout,
    // CORS, réponse illisible) signifie que l'API n'est pas joignable.
    if (error.loginRejected || error.serviceResponse) throw error;
    apiUnreachable = true;
  }

  const demo = DEMO_USERS.find((user) => user.email === identity && user.password === secret);
  if (!demo) {
    throw new Error(
      apiUnreachable
        ? "Le service est momentanément indisponible. Démarrez l'API, ou connectez-vous avec un compte de démonstration."
        : "Identifiants refusés.",
    );
  }
  saveSession({
    email: demo.email,
    name: demo.name,
    role: demo.role,
    token: "demo",
    mode: "demo",
  });
}

/**
 * Branche les boutons qui affichent ou masquent un mot de passe.
 * @param {ParentNode} root
 */
export function bindPasswordToggles(root = document) {
  root.querySelectorAll("[data-toggle-password]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = root.querySelector(button.dataset.togglePassword);
      if (!input) return;
      const next = togglePasswordState(input.type === "text");
      input.type = next.type;
      button.setAttribute("aria-pressed", next.pressed);
      button.setAttribute("aria-label", next.label);
      const icon = button.querySelector(".material-symbols-outlined");
      if (icon) icon.textContent = next.icon;
    });
  });
}

/**
 * Affiche une erreur de formulaire et réactive le bouton d'envoi.
 * @param {HTMLElement | null} error
 * @param {HTMLButtonElement | null} submit
 * @param {string} message
 */
function showLoginError(error, submit, message) {
  if (error) {
    error.textContent = message;
    error.hidden = false;
  }
  if (submit) submit.disabled = false;
}

/**
 * Relie le formulaire de la page de connexion.
 */
function bindLoginPage() {
  const form = document.querySelector("#login-form");
  if (!form) return;
  if (getSession()) {
    location.replace("app.html");
    return;
  }
  bindPasswordToggles(document);
  const error = document.querySelector("#login-error");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    error.hidden = true;
    const submit = form.querySelector("[type=submit]");
    const problem = validateLogin(form.email.value, form.password.value);
    if (problem) {
      showLoginError(error, submit, problem);
      return;
    }
    submit.disabled = true;
    try {
      await login(form.email.value, form.password.value);
      showToast("Connexion acceptée.");
      window.setTimeout(() => location.replace("app.html"), 350);
    } catch (reason) {
      showLoginError(error, submit, reason.message || "Connexion impossible.");
    }
  });
}

if (typeof document !== "undefined") {
  bindLoginPage();
}
