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
    render();
  });
  return select;
}

function renderDashboard(root) {
  const summary = summarize(scopedMeasurements(), scopedPlots());
  const forecast = buildForecast(summary.global.index, summary.global.alerts > 0);
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
    kpi("Indice d'infestation", formatNumber(summary.global.index), LEVEL_LABEL[summary.global.level], summary.global.level),
    kpi("Humidité moyenne", summary.global.humidity === null ? "—" : `${formatNumber(summary.global.humidity)} %`, "24 dernières heures", humidityTone(summary.global.humidity)),
    kpi("Alertes actives", formatNumber(summary.global.alerts, 0), "Parcelles au-delà de 48 h", summary.global.alerts > 0 ? "eleve" : "faible"),
    kpi("Volume sain estimé", `${formatNumber(summary.global.healthyKg, 0)} kg`, "Volume encore commercialisable", "neutral"),
  ]));
  const humidityCanvas = el("canvas");
  const indexCanvas = el("canvas");
  const priceCanvas = el("canvas");
  root.append(el("section", { class: "chart-grid" }, [
    chartCard("Humidité de l'air", "Humidité de l'air sur les dernières heures. Le seuil d'alerte est 85 %.", humidityCanvas),
    chartCard("Indice d'infestation", "Risque estimé à partir de l'humidité et des cabosses touchées.", indexCanvas),
    chartCard("Prix prévisionnel", `Prix indicatif, à partir de ${formatNumber(PRICE_REFERENCE_FCFA_KG, 0)} FCFA/kg, ajusté selon l'indice d'infestation.`, priceCanvas, true),
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
    pageable: meta.rows.length > 8,
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
  root.append(el("ul", { class: "legend" }, [
    el("li", { class: "tone-faible", text: "Faible" }),
    el("li", { class: "tone-modere", text: "Modéré" }),
    el("li", { class: "tone-eleve", text: "Élevé" }),
  ]));
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
  const forecast = buildForecast(summary.global.index, summary.global.alerts > 0);
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
      text: `Estimation indicative : ${formatNumber(PRICE_REFERENCE_FCFA_KG, 0)} FCFA/kg, ajustée selon l'indice d'infestation.`,
    }),
    dataTable(
      ["Date", "Indice", "Référence (FCFA/kg)", "Écart", "Prix (FCFA/kg)"],
      forecast.map((point) => {
        const gap = point.priceFcfaKg - point.reference;
        const signed = `${gap > 0 ? "+" : ""}${formatNumber(gap, 0)}`;
        return [
          point.date,
          formatNumber(point.index),
          formatNumber(point.reference, 0),
          signed,
          formatNumber(point.priceFcfaKg, 0),
        ];
      }),
    ),
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
  state.db = await loadWorkspace();
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
        { name: "name", label: "Nom", value: existing?.name || "" },
        { name: "sector", label: "Secteur", value: existing?.sector || "" },
        { name: "device_id", label: "Appareil", value: existing?.device_id || "AMB-P", hint: "Format AMB-P suivi de 3 chiffres." },
        { name: "reference_volume_kg", label: "Volume de référence (kg)", type: "number", min: 0, step: "1", value: existing?.reference_volume_kg ?? 800 },
      ],
      create: createPlot,
      update: updatePlot,
      done: existing ? "Parcelle modifiée." : "Parcelle créée.",
    },
    device: {
      title: existing ? "Modifier l'appareil" : "Nouvel appareil",
      fields: [
        { name: "device_id", label: "Identifiant", value: existing?.device_id || "AMB-P" },
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
        { name: "name", label: "Nom", value: existing?.name || "" },
        { name: "email", label: "E-mail", type: "email", autocomplete: "off", value: existing?.email || "" },
        {
          name: "role",
          label: "Rôle",
          type: "select",
          value: existing?.role || "acheteur",
          options: [
            { value: "acheteur", label: "Acheteur" },
            { value: "admin", label: "Administrateur" },
          ],
        },
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
      if (existing) await form.update(existing.id, values);
      else await form.create(values);
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
      message: `${record.name} : la parcelle, l'appareil lié et les mesures associées seront retirés.`,
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
      message: `${record.name} sera retiré de l'annuaire.`,
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
    state.db = await loadWorkspace();
  } catch (error) {
    state.db = { version: 1, plots: [], devices: [], subscribers: [], measurements: [] };
    showToast(error.message || "Chargement impossible.", "error");
  }
  show("dashboard");
}

init();
