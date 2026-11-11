/**
 * Rôle : tableau de bord, mesures, gestion et lecture terrain.
 * Auteur : NEGOUE Patrick
 * Bloc : B (MOD-B3, MOD-B4)
 */

import {
  createDevice,
  createPlot,
  createSubscriber,
  deleteDevice,
  deletePlot,
  deleteSubscriber,
  loadIndicators,
  loadWorkspace,
  resetDemoDb,
  updateDevice,
  updatePlot,
  updateSubscriber,
} from "./api.js";
import { destroyCharts, renderCharts } from "./charts.js";
import { LEVEL_LABEL, formatDateTime, formatNumber, formatPercent } from "./format.js";
import { cell, mountGrid } from "./grids.js";
import {
  HUMIDITY_ALERT,
  PRICE_FORMULA_VERSION,
  PRICE_REFERENCE_FCFA_KG,
  buildForecast,
  seriesByHour,
  summarize,
} from "./metrics.js";
import { openConfirm, openForm } from "./modals.js";
import { showToast } from "./toast.js";
import { getSession, logout } from "./auth.js";

const TITLES = {
  dashboard: "Tableau de bord",
  mesures: "Mesures",
  parcelles: "Parcelles",
  appareils: "Appareils",
  abonnes: "Abonnés",
  terrain: "Lecture terrain",
  journal: "Journal des prix",
};

const state = {
  session: null,
  db: null,
  // Indicateurs du serveur (/api/v1/kpis et /prices/forecast) ; null en démo.
  indicators: null,
  view: "dashboard",
  plotId: "all",
  search: "",
  selectedId: null,
};

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => {
    if (value === undefined || value === null || value === false) return;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = String(value);
    else node.setAttribute(key, String(value));
  });
  children.forEach((child) => {
    if (child) node.append(child);
  });
  return node;
}

function icon(name) {
  return el("span", { class: "material-symbols-outlined", "aria-hidden": "true", text: name });
}

function canWrite() {
  return state.session?.role === "admin";
}

function scopedPlots() {
  if (state.plotId === "all") return state.db.plots;
  return state.db.plots.filter((plot) => plot.id === state.plotId);
}

function scopedMeasurements() {
  const ids = new Set(scopedPlots().map((plot) => plot.device_id));
  return state.db.measurements.filter((item) => ids.has(item.device_id));
}

function plotByDevice(deviceId) {
  return state.db.plots.find((plot) => plot.device_id === deviceId) || null;
}

function pill(level, label) {
  return `<div class="grid-cell"><span class="pill pill-${level}">${label}</span></div>`;
}

function hotCell(value, formatted) {
  const cls = Number(value) > HUMIDITY_ALERT ? "grid-cell is-hot" : "grid-cell";
  return `<div class="${cls}">${formatted}</div>`;
}

function plotFilter() {
  const select = el("select", { "aria-label": "Filtrer par parcelle" });
  select.append(el("option", { value: "all", text: "Toutes les parcelles" }));
  state.db.plots.forEach((plot) => {
    const option = el("option", { value: plot.id, text: plot.name });
    select.append(option);
  });
  if (state.plotId !== "all" && !state.db.plots.some((plot) => plot.id === state.plotId)) {
    state.plotId = "all";
  }
  select.value = state.plotId;
  select.addEventListener("change", () => {
    state.plotId = select.value;
    // Les KPIs sont filtrés côté serveur : on les recharge pour la parcelle.
    reload().catch((error) => showToast(error.message || "Chargement impossible.", "error"));
  });
  return select;
}

/** Indicateurs du serveur, ou null quand le dashboard calcule en local. */
function indicators() {
  return state.indicators;
}

/** Courbe de prix : celle de l'API si elle est disponible, sinon calcul local. */
function priceForecast(index, alerts) {
  const fromApi = indicators()?.forecast?.points;
  if (Array.isArray(fromApi) && fromApi.length > 0) return fromApi;
  return buildForecast(index, alerts > 0);
}

function renderDashboard(root) {
  const summary = summarize(scopedMeasurements(), scopedPlots());
  const kpis = indicators()?.kpis ?? null;
  const index = kpis ? kpis.global_infestation_index : summary.global.index;
  const level = kpis ? kpis.level : summary.global.level;
  const humidity = kpis ? kpis.avg_air_humidity_pct : summary.global.humidity;
  const alerts = kpis ? kpis.active_alerts : summary.global.alerts;
  const healthyKg = kpis ? kpis.estimated_healthy_volume_kg : summary.global.healthyKg;
  const forecast = priceForecast(index, alerts);
  const reference = forecast[0]?.reference ?? PRICE_REFERENCE_FCFA_KG;
  const formula = indicators()?.forecast?.formulaVersion || PRICE_FORMULA_VERSION;
  const alertNames = summary.plots.filter((plot) => plot.alert).map((plot) => plot.name);
  root.append(el("div", { class: "view-head" }, [
    el("p", { class: "lede", text: "Risque d'infestation, humidité et volume de cacao encore sain." }),
    plotFilter(),
  ]));
  if (alertNames.length > 0) {
    root.append(el("p", {
      class: "banner banner-danger",
      text: `${alertNames.join(", ")} : humidité supérieure à 85 % depuis plus de 48 h. Baisse du volume sain anticipée sous 7 jours.`,
    }));
  }
  root.append(el("section", { class: "kpi-grid" }, [
    kpi("Indice d'infestation", formatNumber(index), LEVEL_LABEL[level], level),
    kpi("Humidité moyenne", humidity === null ? "—" : `${formatNumber(humidity)} %`, "24 dernières heures", humidityTone(humidity)),
    kpi("Alertes actives", formatNumber(alerts, 0), "Parcelles au-delà de 48 h", alerts > 0 ? "eleve" : "faible"),
    kpi(
      "Volume sain estimé",
      healthyKg > 0 ? `${formatNumber(healthyKg, 0)} kg` : "—",
      kpis && healthyKg > 0
        ? `${formatNumber(kpis.estimated_healthy_volume_pct, 0)} % du volume de référence`
        : "Renseignez le volume de référence des parcelles",
      "neutral",
    ),
  ]));
  root.append(el("p", {
    class: "caption",
    text: kpis
      ? "Indicateurs fournis par GET /api/v1/kpis."
      : "Indicateurs calculés localement (mode démonstration, formules RM2/RM3 identiques à l'API).",
  }));
  const humidityCanvas = el("canvas");
  const indexCanvas = el("canvas");
  const priceCanvas = el("canvas");
  root.append(el("section", { class: "chart-grid" }, [
    chartCard("Humidité de l'air", "Humidité de l'air sur les dernières heures. Le seuil d'alerte est 85 %.", humidityCanvas),
    chartCard("Indice d'infestation", "Risque estimé à partir de l'humidité et des cabosses touchées.", indexCanvas),
    chartCard("Prix prévisionnel", `Prix indicatif, à partir de ${formatNumber(reference, 0)} FCFA/kg, ajusté selon l'indice d'infestation (formule ${formula}).`, priceCanvas, true),
  ]));
  const drawn = renderCharts({
    humidityCanvas,
    indexCanvas,
    priceCanvas,
    series: seriesByHour(scopedMeasurements(), scopedPlots()),
    forecast,
  });
  if (!drawn) {
    root.append(el("p", { class: "empty", text: "Aucune mesure sur cette sélection." }));
  }
}

function kpi(label, value, detail, tone) {
  return el("article", { class: `kpi tone-${tone || "neutral"}` }, [
    el("p", { class: "kpi-label", text: label }),
    el("p", { class: "kpi-value", text: value }),
    el("p", { class: "kpi-detail", text: detail }),
  ]);
}

function humidityTone(value) {
  if (value === null || value <= 75) return "faible";
  if (value <= HUMIDITY_ALERT) return "modere";
  return "eleve";
}

function chartCard(title, caption, canvas, wide = false) {
  return el("article", { class: wide ? "chart-card wide" : "chart-card" }, [
    el("h2", { text: title }),
    el("p", { class: "caption", text: caption }),
    el("div", { class: "chart-box" }, [canvas]),
  ]);
}

function renderMesures(root) {
  root.append(el("div", { class: "view-head" }, [
    el("p", { class: "lede", text: "Température, humidité et diagnostic transmis par les boîtiers." }),
    plotFilter(),
  ]));
  const search = el("input", {
    type: "search",
    placeholder: "Rechercher une parcelle ou un appareil",
    "aria-label": "Rechercher une mesure",
    value: state.search,
  });
  root.append(el("div", { class: "toolbar" }, [search]));
  const holder = el("div", { class: "grid-holder", id: "measure-grid" });
  root.append(holder);
  const paint = () => {
    const query = state.search.trim().toLowerCase();
    const rows = scopedMeasurements()
      .map((item) => ({
        id: item.id,
        timestamp: item.timestamp,
        plot_name: plotByDevice(item.device_id)?.name || "—",
        device_id: item.device_id,
        temperature_c: item.climate.temperature_c,
        air_humidity_pct: item.climate.air_humidity_pct,
        soil_humidity_pct: item.climate.soil_humidity_pct,
        detected: item.diagnostic_ia.phytophthora_detected,
        confidence: item.diagnostic_ia.confidence,
      }))
      .filter((row) => {
        if (!query) return true;
        return `${row.plot_name} ${row.device_id}`.toLowerCase().includes(query);
      })
      .sort((a, b) => b.timestamp - a.timestamp);
    mountGrid(holder, [
      { field: "timestamp", label: "Horodatage", type: "number", width: "16%", render: (value) => cell(formatDateTime(value)) },
      { field: "plot_name", label: "Parcelle", width: "14%", render: (value) => cell(value) },
      { field: "device_id", label: "Appareil", width: "12%", render: (value) => cell(value) },
      { field: "temperature_c", label: "Température", type: "number", width: "12%", render: (value) => cell(`${formatNumber(value)} °C`) },
      { field: "air_humidity_pct", label: "Air", type: "number", width: "12%", render: (value) => hotCell(value, `${formatNumber(value)} %`) },
      { field: "soil_humidity_pct", label: "Sol", type: "number", width: "12%", render: (value) => cell(`${formatNumber(value)} %`) },
      {
        field: "detected",
        label: "Pourriture",
        type: "number",
        width: "12%",
        render: (value) => pill(value === 1 ? "eleve" : "faible", value === 1 ? "Détectée" : "Saine"),
      },
      { field: "confidence", label: "Confiance", type: "number", width: "10%", render: (value) => cell(formatNumber(value, 2)) },
    ], rows, { filterable: true, pageable: true, height: 430 });
  };
  search.addEventListener("input", () => {
    state.search = search.value;
    paint();
  });
  paint();
}

function renderEntity(root, kind) {
  const meta = {
    plot: {
      title: "Parcelles suivies et niveau de risque de chacune.",
      create: "Nouvelle parcelle",
      columns: plotColumns(),
      rows: plotRows(),
    },
    device: {
      title: "Boîtiers rattachés aux parcelles.",
      create: "Nouvel appareil",
      columns: deviceColumns(),
      rows: deviceRows(),
    },
    subscriber: {
      title: "Abonnés autorisés à consulter le service.",
      create: "Nouvel abonné",
      columns: subscriberColumns(),
      rows: subscriberRows(),
    },
  }[kind];
  const head = el("div", { class: "view-head" }, [el("p", { class: "lede", text: meta.title })]);
  root.append(head);
  if (canWrite()) {
    root.append(el("div", { class: "toolbar" }, [
      el("button", { type: "button", class: "btn btn-primary", "data-action": "create", text: meta.create }),
      el("button", { type: "button", class: "btn btn-ghost", id: "edit-entity", "data-action": "edit", disabled: "disabled", text: "Modifier" }),
      el("button", { type: "button", class: "btn btn-danger", id: "delete-entity", "data-action": "delete", disabled: "disabled", text: "Supprimer" }),
    ]));
  }
  const holder = el("div", { class: "grid-holder", id: "entity-grid" });
  root.append(holder);
  mountGrid(holder, meta.columns, meta.rows, {
    filterable: true,
    pageable: true,
    height: 420,
    onSelect: (row) => {
      state.selectedId = row?.id || row?.boundindex && meta.rows[row.boundindex]?.id || null;
      if (row?.id) state.selectedId = row.id;
      document.querySelector("#edit-entity")?.toggleAttribute("disabled", !state.selectedId);
      document.querySelector("#delete-entity")?.toggleAttribute("disabled", !state.selectedId);
    },
  });
}

function plotRows() {
  const summary = summarize(state.db.measurements, state.db.plots);
  return summary.plots.map((plot) => ({
    id: plot.id,
    name: plot.name,
    village: plot.village || "—",
    surface_ha: plot.surface_ha,
    sector: plot.sector,
    device_id: plot.device_id,
    hours: plot.hours,
    rate: plot.rate,
    index: plot.index,
    level: plot.level,
    healthyKg: plot.healthyKg,
  }));
}

function plotColumns() {
  return [
    { field: "name", label: "Parcelle", render: (value) => cell(value) },
    { field: "village", label: "Village", render: (value) => cell(value) },
    { field: "surface_ha", label: "Surface", type: "number", render: (value) => cell(`${formatNumber(value, 1)} ha`) },
    { field: "sector", label: "Secteur", render: (value) => cell(value) },
    { field: "device_id", label: "Appareil", render: (value) => cell(value) },
    { field: "hours", label: "Heures > 85 %", type: "number", render: (value) => cell(formatNumber(value, 0)) },
    { field: "rate", label: "Détections", type: "number", render: (value) => cell(formatPercent(value)) },
    { field: "index", label: "Indice", type: "number", render: (value) => cell(formatNumber(value)) },
    { field: "level", label: "Niveau", render: (value) => pill(value, LEVEL_LABEL[value] || value) },
    { field: "healthyKg", label: "Volume sain", type: "number", render: (value) => cell(`${formatNumber(value, 0)} kg`) },
  ];
}

function deviceRows() {
  return state.db.devices.map((device) => ({
    id: device.id,
    device_id: device.device_id,
    plot_name: state.db.plots.find((plot) => plot.id === device.plot_id)?.name || "—",
    status: device.status,
  }));
}

function deviceColumns() {
  return [
    { field: "device_id", label: "Identifiant", render: (value) => cell(value) },
    { field: "plot_name", label: "Parcelle", render: (value) => cell(value) },
    {
      field: "status",
      label: "Statut",
      render: (value) => pill(value === "actif" ? "faible" : "modere", value === "actif" ? "Actif" : "Hors ligne"),
    },
  ];
}

function subscriberRows() {
  return state.db.subscribers.map((item) => ({
    id: item.id,
    name: item.name,
    email: item.email,
    role: item.role,
    plan: item.plan,
  }));
}

function subscriberColumns() {
  return [
    { field: "name", label: "Nom", render: (value) => cell(value) },
    { field: "email", label: "E-mail", render: (value) => cell(value) },
    {
      field: "role",
      label: "Rôle",
      render: (value) => cell(value === "admin" ? "Administrateur" : "Acheteur"),
    },
    { field: "plan", label: "Formule", render: (value) => cell(value) },
  ];
}

function renderTerrain(root) {
  const summary = summarize(scopedMeasurements(), scopedPlots());
  const focus = [...summary.plots].sort((a, b) => b.index - a.index)[0];
  root.append(el("div", { class: "view-head" }, [
    el("p", { class: "lede", text: "État sanitaire de la parcelle." }),
    plotFilter(),
  ]));
  if (!focus) {
    root.append(el("p", { class: "empty", text: "Aucune parcelle à afficher." }));
    return;
  }
  root.append(el("p", { class: "terrain-name", text: focus.name }));
  // Feu d'alerte : l'état se lit à la couleur et au pictogramme, sans texte.
  root.append(
    el(
      "div",
      {
        class: `terrain-signal tone-${focus.level}`,
        role: "img",
        "aria-label": `Niveau d'alerte : ${LEVEL_LABEL[focus.level]}${focus.alert ? ", pulvérisation recommandée" : ""}`,
      },
      [icon(focus.alert ? "warning" : "check_circle")],
    ),
  );
  root.append(el("section", { class: "terrain-grid" }, [
    terrainTile("water_drop", focus.humidity === null ? "—" : formatNumber(focus.humidity), "Humidité de l'air, en pour cent", humidityTone(focus.humidity)),
    terrainTile("eco", formatNumber(focus.index), `Indice ${LEVEL_LABEL[focus.level]}`, focus.level),
    terrainTile(
      focus.alert ? "pest_control" : "check",
      formatNumber(focus.hours, 0),
      focus.alert ? "Alerte de pulvérisation" : "Pas d'alerte de pulvérisation",
      focus.alert ? "eleve" : "faible",
    ),
  ]));
  root.append(
    el("div", { class: "terrain-actions" }, [
      terrainAction("volume_up", "Écouter", "Écouter l'alerte à voix haute", () => speakAlert(focus)),
      terrainAction("call", "Appeler", "Appeler le conseiller agricole", () => {
        showToast("Conseiller agricole : +237 6 90 00 00 00", "success");
      }),
    ]),
  );
  root.append(el("ul", { class: "legend" }, [
    el("li", { class: "tone-faible", text: "Faible" }),
    el("li", { class: "tone-modere", text: "Modéré" }),
    el("li", { class: "tone-eleve", text: "Élevé" }),
  ]));
}

/** Gros bouton muet : un pictogramme et un mot, lisible en plein soleil. */
function terrainAction(symbol, label, ariaLabel, onClick) {
  const button = el("button", { type: "button", class: "terrain-action", "aria-label": ariaLabel }, [
    icon(symbol),
    el("strong", { text: label }),
  ]);
  button.addEventListener("click", onClick);
  return button;
}

/** Lit l'état de la parcelle à voix haute, pour un utilisateur qui ne lit pas. */
function speakAlert(focus) {
  const niveau = LEVEL_LABEL[focus.level] ?? "Inconnu";
  const phrase = focus.alert
    ? `Alerte ${niveau}. Parcelle ${focus.name} : humidité ${formatNumber(focus.humidity)} pour cent. Pulvérisation recommandée.`
    : `Niveau ${niveau}. Parcelle ${focus.name} : humidité ${formatNumber(focus.humidity)} pour cent. Pas d'alerte.`;
  if (!("speechSynthesis" in window)) {
    showToast("La lecture vocale n'est pas disponible dans ce navigateur.", "error");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(phrase);
  utterance.lang = "fr-FR";
  window.speechSynthesis.speak(utterance);
}

function terrainTile(symbol, figure, caption, tone) {
  return el("article", { class: `terrain-tile tone-${tone}` }, [
    icon(symbol),
    el("strong", { text: figure }),
    el("span", { class: "sr-only", text: caption }),
  ]);
}

function renderJournal(root) {
  const summary = summarize(scopedMeasurements(), scopedPlots());
  const kpis = indicators()?.kpis ?? null;
  const index = kpis ? kpis.global_infestation_index : summary.global.index;
  const alerts = kpis ? kpis.active_alerts : summary.global.alerts;
  const forecast = priceForecast(index, alerts);
  const reference = forecast[0]?.reference ?? PRICE_REFERENCE_FCFA_KG;
  const formula = indicators()?.forecast?.formulaVersion || PRICE_FORMULA_VERSION;
  const hasIndex = forecast.some((point) => Number.isFinite(point.index));
  const headers = hasIndex
    ? ["Date", "Indice", "Référence (FCFA/kg)", "Écart", "Prix (FCFA/kg)"]
    : ["Date", "Référence (FCFA/kg)", "Écart", "Prix (FCFA/kg)"];
  const rows = forecast.map((point) => {
    const values = [point.date];
    if (hasIndex) values.push(point.index === undefined ? "—" : formatNumber(point.index));
    const gap = point.priceFcfaKg - point.reference;
    values.push(
      formatNumber(point.reference, 0),
      `${gap > 0 ? "+" : ""}${formatNumber(gap, 2)}`,
      formatNumber(point.priceFcfaKg, 0),
    );
    return values;
  });
  root.append(el("div", { class: "view-head" }, [
    el("p", { class: "lede", text: "Détail des prix prévisionnels proposés aux acheteurs." }),
    plotFilter(),
  ]));
  root.append(el("section", { class: "panel" }, [
    el("h2", { text: "Situation des parcelles" }),
    dataTable(
      ["Parcelle", "Heures > 85 %", "Détections", "Indice", "Alerte"],
      summary.plots.map((plot) => [
        plot.name,
        formatNumber(plot.hours, 0),
        formatPercent(plot.rate),
        formatNumber(plot.index),
        plot.alert ? "Oui" : "Non",
      ]),
    ),
  ]));
  root.append(el("section", { class: "panel" }, [
    el("h2", { text: "Prix prévisionnel" }),
    el("p", {
      class: "caption",
      text: `Estimation indicative : ${formatNumber(reference, 0)} FCFA/kg, ajustée selon l'indice d'infestation (formule ${formula}). Source : ${
        indicators()?.forecast ? "GET /api/v1/prices/forecast" : "calcul local, mode démonstration"
      }.`,
    }),
    dataTable(headers, rows),
  ]));
}

function dataTable(headers, rows) {
  const table = el("table", { class: "data" });
  const head = el("tr");
  headers.forEach((header) => head.append(el("th", { scope: "col", text: header })));
  table.append(el("thead", {}, [head]));
  const body = el("tbody");
  rows.forEach((row) => {
    const tr = el("tr");
    row.forEach((value) => tr.append(el("td", { text: value })));
    body.append(tr);
  });
  table.append(body);
  return el("div", { class: "table-scroll" }, [table]);
}

function render() {
  destroyCharts();
  const root = document.querySelector("#view");
  root.replaceChildren();
  if (!state.db) return;
  if (state.view === "dashboard") renderDashboard(root);
  else if (state.view === "mesures") renderMesures(root);
  else if (state.view === "parcelles") renderEntity(root, "plot");
  else if (state.view === "appareils") renderEntity(root, "device");
  else if (state.view === "abonnes") renderEntity(root, "subscriber");
  else if (state.view === "terrain") renderTerrain(root);
  else if (state.view === "journal") renderJournal(root);
}

/** Ouvre ou ferme le menu latéral sur petit écran. */
function setMenuOpen(open) {
  document.body.classList.toggle("nav-open", open);
  document.querySelectorAll(".menu-btn").forEach((button) => {
    button.setAttribute("aria-expanded", String(open));
    button.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
  });
}

function show(view) {
  state.view = view;
  state.selectedId = null;
  setMenuOpen(false);
  document.querySelectorAll("[data-nav]").forEach((button) => {
    const active = button.dataset.nav === view;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  document.querySelector("#view-title").textContent = TITLES[view];
  document.title = `${TITLES[view]} · AGRO-DATA`;
  render();
}

function kindOfView() {
  if (state.view === "parcelles") return "plot";
  if (state.view === "appareils") return "device";
  if (state.view === "abonnes") return "subscriber";
  return null;
}

function recordById(kind, id) {
  const list = kind === "plot" ? state.db.plots : kind === "device" ? state.db.devices : state.db.subscribers;
  return list.find((item) => item.id === id) || null;
}

async function reload() {
  const db = await loadWorkspace();
  let fromApi = null;
  try {
    fromApi = await loadIndicators({ plotId: state.plotId });
  } catch (error) {
    // Les grilles restent utilisables : on retombe sur le calcul local.
    showToast(error.message || "Indicateurs indisponibles.", "error");
  }
  state.db = db;
  state.indicators = fromApi;
  render();
}

async function saveEntity(kind, existing) {
  if (kind === "device" && state.db.plots.length === 0) {
    showToast("Créez d'abord une parcelle.", "error");
    return;
  }
  const forms = {
    plot: {
      title: existing ? "Modifier la parcelle" : "Nouvelle parcelle",
      fields: [
        { name: "code", label: "Code", value: existing?.code || "", readOnly: Boolean(existing), hint: "2 à 32 caractères : lettres, chiffres et tirets. Exemple : P-EST." },
        { name: "name", label: "Nom", value: existing?.name || "" },
        { name: "location_label", label: "Secteur", value: existing?.sector || "" },
        { name: "village", label: "Village", value: existing?.village || "", hint: "Village où se trouve la parcelle." },
        { name: "surface_ha", label: "Surface (ha)", type: "number", step: "0.1", min: 0.1, value: existing?.surface_ha || "", hint: "Surface cultivée, supérieure à 0." },
        { name: "reference_volume_kg", label: "Volume de référence (kg)", type: "number", step: "1", min: 0, value: existing?.reference_volume_kg ?? 0, hint: "Production attendue : base du volume sain affiché." },
      ],
      create: createPlot,
      update: updatePlot,
      done: existing ? "Parcelle modifiée." : "Parcelle créée.",
    },
    device: {
      title: existing ? "Modifier l'appareil" : "Nouvel appareil",
      fields: [
        { name: "device_id", label: "Identifiant", value: existing?.device_id || "AMB-P", hint: "Format AMB-P suivi de 3 chiffres." },
        { name: "label", label: "Libellé", value: existing?.label || "" },
        {
          name: "plot_id",
          label: "Parcelle",
          type: "select",
          value: existing?.plot_id || state.db.plots[0]?.id,
          options: state.db.plots.map((plot) => ({ value: plot.id, label: plot.name })),
        },
        {
          name: "status",
          label: "Statut",
          type: "select",
          value: existing?.status || "actif",
          options: [
            { value: "actif", label: "Actif" },
            { value: "hors_ligne", label: "Hors ligne" },
          ],
        },
      ],
      create: createDevice,
      update: updateDevice,
      done: existing ? "Appareil modifié." : "Appareil créé.",
    },
    subscriber: {
      title: existing ? "Modifier l'abonné" : "Nouvel abonné",
      fields: [
        { name: "organization", label: "Organisation", value: existing?.name || "" },
        { name: "email", label: "E-mail", type: "email", autocomplete: "off", value: existing?.email || "", readOnly: Boolean(existing) },
        {
          name: "plan",
          label: "Formule",
          type: "select",
          value: existing?.plan || "Marché",
          options: [
            { value: "Marché", label: "Marché" },
            { value: "Exploitation", label: "Exploitation" },
            { value: "Lecture", label: "Lecture" },
          ],
        },
      ],
      create: createSubscriber,
      update: updateSubscriber,
      done: existing ? "Abonné modifié." : "Abonné créé.",
    },
  };
  const form = forms[kind];
  await openForm({
    title: form.title,
    submitLabel: existing ? "Enregistrer" : "Créer",
    fields: form.fields,
    onSubmit: async (values) => {
      if (existing) await form.update(existing.id, values, state.db);
      else await form.create(values, state.db);
      showToast(form.done);
      await reload();
      return null;
    },
  });
}

async function removeEntity(kind, record) {
  const messages = {
    plot: {
      title: "Supprimer la parcelle",
      message: `${record.name} sera retirée de la liste des parcelles.`,
      confirm: "Supprimer",
      toast: "Parcelle supprimée.",
      run: deletePlot,
    },
    device: {
      title: "Supprimer l'appareil",
      message: `${record.device_id} sera retiré de la liste des boîtiers.`,
      confirm: "Supprimer",
      toast: "Appareil supprimé.",
      run: deleteDevice,
    },
    subscriber: {
      title: "Supprimer l'abonné",
      message: `${record.name || record.email} sera retiré de l'annuaire.`,
      confirm: "Supprimer",
      toast: "Abonné supprimé.",
      run: deleteSubscriber,
    },
  };
  const spec = messages[kind];
  const accepted = await openConfirm({ title: spec.title, message: spec.message, confirmLabel: spec.confirm });
  if (!accepted) return;
  await spec.run(record.id);
  showToast(spec.toast);
  state.selectedId = null;
  await reload();
}

async function onClick(event) {
  const nav = event.target.closest("[data-nav]");
  if (nav) {
    show(nav.dataset.nav);
    return;
  }
  const actionEl = event.target.closest("[data-action]");
  if (!actionEl || actionEl.disabled) return;
  const action = actionEl.dataset.action;
  if (action === "menu") {
    setMenuOpen(!document.body.classList.contains("nav-open"));
    return;
  }
  if (action === "theme") {
    toggleTheme();
    return;
  }
  if (action === "logout") {
    logout();
    location.href = "index.html";
    return;
  }
  if (action === "reset-demo") {
    const accepted = await openConfirm({
      title: "Rétablir les données",
      message: "Les parcelles et mesures ajoutées seront remplacées par les données initiales.",
      confirmLabel: "Réinitialiser",
    });
    if (!accepted) return;
    resetDemoDb();
    state.plotId = "all";
    state.search = "";
    await reload();
    showToast("Données initiales rétablies.");
    return;
  }
  const kind = kindOfView();
  if (!kind || !canWrite()) return;
  try {
    if (action === "create") await saveEntity(kind, null);
    if (action === "edit" || action === "delete") {
      const record = recordById(kind, state.selectedId);
      if (!record) return;
      if (action === "edit") await saveEntity(kind, record);
      if (action === "delete") await removeEntity(kind, record);
    }
  } catch (error) {
    showToast(error.message || "Action impossible.", "error");
  }
}

/**
 * Bascule clair/sombre comme la maquette : lit le schéma appliqué, puis force
 * data-theme sur <html>. Le choix est mémorisé pour survivre à un rechargement
 * (la maquette ne le faisait pas). Les graphiques sont retracés avec les
 * nouveaux jetons.
 */
const THEME_KEY = "agro-data-theme";

function toggleTheme() {
  const root = document.documentElement;
  const dark = getComputedStyle(root).colorScheme === "dark";
  const next = dark ? "light" : "dark";
  root.dataset.theme = next;
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch (error) {
    /* stockage indisponible : le thème reste actif pour la session */
  }
  render();
}

async function init() {
  const session = getSession();
  if (!session) {
    location.replace("index.html");
    return;
  }
  state.session = session;
  document.querySelector("#user-name").textContent = session.name;
  document.querySelector("#user-role").textContent = session.role === "admin" ? "Administrateur" : "Acheteur";
  document.querySelector("#mode-label").textContent = session.mode === "demo" ? "Données de démonstration" : "Connecté au service";
  if (session.mode === "demo" && session.role === "admin") {
    document.querySelector("#reset-demo").hidden = false;
  }
  document.body.addEventListener("click", (event) => {
    onClick(event).catch((error) => showToast(error.message || "Action impossible.", "error"));
  });
  try {
    await reload();
  } catch (error) {
    state.db = { version: 1, plots: [], devices: [], subscribers: [], measurements: [] };
    state.indicators = null;
    showToast(error.message || "Chargement impossible.", "error");
  }
  show("dashboard");
}

init();
