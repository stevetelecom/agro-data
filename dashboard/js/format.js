/**
 * Rôle : format d'affichage et échappement des textes saisis.
 * Auteur : NEGOUE Patrick
 * Bloc : B
 */

const dateTime = new Intl.DateTimeFormat("fr-FR", {
  timeZone: "Africa/Douala",
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

const numberFormat = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const integerFormat = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

export const LEVEL_LABEL = {
  faible: "Faible",
  modere: "Modéré",
  eleve: "Élevé",
};

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function formatDateTime(unixSeconds) {
  return dateTime.format(new Date(Number(unixSeconds) * 1000));
}

export function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  if (digits === 0) return integerFormat.format(Number(value));
  if (digits === 1) return numberFormat.format(Number(value));
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

export function formatPercent(rate) {
  if (rate === null || rate === undefined || Number.isNaN(Number(rate))) return "—";
  return `${formatNumber(Number(rate) * 100, 0)} %`;
}
