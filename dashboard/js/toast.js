/**
 * Rôle : notification de confirmation après une action validée.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3)
 */

export function showToast(message, variant = "success") {
  const root = document.querySelector("#toast-root");
  if (!root) return;
  const item = document.createElement("div");
  item.className = `toast toast-${variant}`;
  item.setAttribute("role", "status");
  const icon = document.createElement("span");
  icon.className = "material-symbols-outlined";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = variant === "success" ? "check_circle" : "error";
  const text = document.createElement("p");
  text.textContent = message;
  item.append(icon, text);
  root.append(item);
  window.setTimeout(() => item.remove(), 4200);
}
