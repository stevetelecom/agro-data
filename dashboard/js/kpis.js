// Rôle : page KPIs (tableau de bord) et vue producteur « zéro-texte ».
// Contrat consommé : docs/CONTRAT_JSON.md §4.4 (GET /api/v1/kpis).
// Auteur : MEKONTSO Olivier Steve (MOD-B2, issue #15).
//
// La page tente d'abord l'API réelle avec le jeton de session. Si l'API n'est
// pas joignable (backend non démarré, PR #25 non fusionnée), elle bascule sur
// un jeu de démonstration conforme au contrat et l'affiche explicitement :
// la démonstration du 11/11 ne dépend donc pas du backend.

"use strict";

const API_BASE = window.AGRO_API_BASE ?? "http://127.0.0.1:8000";
const TOKEN_KEY = "agro_token";
const THEME_KEY = "agro_theme";
const FENETRE_JOURS = 7;
const DELAI_API_MS = 4000;

const $ = (selecteur, racine = document) => racine.querySelector(selecteur);

/** Échappe le texte inséré dans du HTML. */
function esc(valeur) {
  return String(valeur).replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );
}

/** Formate un nombre à la française, sans décimale inutile. */
function nombre(valeur, decimales = 1) {
  const n = Number(valeur);
  if (!Number.isFinite(n)) return "—";
  return new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimales,
  }).format(n);
}

/** Traduit le niveau du contrat en libellé, classe CSS et icône. */
function niveau(niveauApi) {
  switch (niveauApi) {
    case "faible":
      return { libelle: "Faible", classe: "ok", icone: "sentiment_satisfied", couleur: "var(--ok)" };
    case "eleve":
      return { libelle: "Élevé", classe: "ko", icone: "dangerous", couleur: "var(--ko)" };
    default:
      return { libelle: "Modéré", classe: "mod", icone: "warning", couleur: "var(--mod)" };
  }
}

/** Date courte JJ/MM à partir d'une date ISO. */
function jourCourt(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return String(iso);
  return `${String(d.getUTCDate()).padStart(2, "0")}/${String(d.getUTCMonth() + 1).padStart(2, "0")}`;
}

/* ===== Jeu de démonstration (contrat §4.4, données de la maquette) ===== */

const JOURS_DEMO = ["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"];

function serieDemo(plotId, nom, sousAlerte, valeurs) {
  return {
    plot_id: plotId,
    plot_name: nom,
    under_alert: sousAlerte,
    points: valeurs.map((valeur, i) => ({ date: JOURS_DEMO[i], air_humidity_pct: valeur })),
  };
}

const KPIS_DEMO = {
  global_infestation_index: 47,
  level: "modere",
  active_alerts: 2,
  avg_air_humidity_pct: 84.4,
  humidity_delta_7d: 4.0,
  estimated_healthy_volume_pct: 67,
  plots_monitored: 4,
  generated_at: "2026-11-10T11:00:00Z",
  humidity_series: [
    serieDemo(1, "Parcelle Nkoulou", true, [78, 80, 83, 86, 88, 87, 89]),
    serieDemo(2, "Parcelle Ntem Nord", false, [72, 74, 73, 75, 76, 74, 75]),
  ],
};

// Courbe de prix de démonstration (contrat §4.5, formule RM3 v1).
const INDICES_DEMO = [0, 8, 14, 28, 42, 55, 62];
const PRIX_DEMO = {
  unit: "FCFA/kg",
  horizon_days: JOURS_DEMO.length,
  is_demo: true,
  formula_version: "v1",
  points: JOURS_DEMO.map((date, i) => ({
    date,
    reference_price: 1050,
    adjusted_price: Math.round(1050 * (1 + 0.15 * INDICES_DEMO[i] / 100) * 100) / 100,
  })),
};

/* ===== Accès aux données ===== */

/**
 * Charge les KPIs : API réelle si un jeton existe, sinon démonstration.
 * @returns {Promise<{donnees: object, source: "api"|"demo", motif: string}>}
 */
async function chargerKpis() {
  const jeton = localStorage.getItem(TOKEN_KEY);
  if (!jeton) {
    return { donnees: KPIS_DEMO, source: "demo", motif: "aucun jeton de session" };
  }

  const controleur = new AbortController();
  const minuteur = setTimeout(() => controleur.abort(), DELAI_API_MS);
  try {
    const reponse = await fetch(`${API_BASE}/api/v1/kpis?days=${FENETRE_JOURS}`, {
      headers: { Authorization: `Bearer ${jeton}` },
      signal: controleur.signal,
    });
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    return { donnees: await reponse.json(), source: "api", motif: "" };
  } catch (erreur) {
    console.warn("KPIs indisponibles, repli sur les données de démonstration :", erreur.message);
    return { donnees: KPIS_DEMO, source: "demo", motif: erreur.message };
  } finally {
    clearTimeout(minuteur);
  }
}

/**
 * Charge la courbe de prix : API réelle si un jeton existe, sinon démonstration.
 * @returns {Promise<{donnees: object, source: "api"|"demo", motif: string}>}
 */
async function chargerPrix() {
  const jeton = localStorage.getItem(TOKEN_KEY);
  if (!jeton) {
    return { donnees: PRIX_DEMO, source: "demo", motif: "aucun jeton de session" };
  }

  const controleur = new AbortController();
  const minuteur = setTimeout(() => controleur.abort(), DELAI_API_MS);
  try {
    const reponse = await fetch(`${API_BASE}/api/v1/prices/forecast?days=${FENETRE_JOURS}`, {
      headers: { Authorization: `Bearer ${jeton}` },
      signal: controleur.signal,
    });
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    return { donnees: await reponse.json(), source: "api", motif: "" };
  } catch (erreur) {
    console.warn("Courbe de prix indisponible, repli sur la démonstration :", erreur.message);
    return { donnees: PRIX_DEMO, source: "demo", motif: erreur.message };
  } finally {
    clearTimeout(minuteur);
  }
}

/* ===== Graphique ===== */

/**
 * Construit un graphique linéaire SVG accessible.
 * @param {Array} series séries du contrat (points = {date, air_humidity_pct})
 * @param {{seuil?: number, min?: number, max?: number}} options
 */
function graphiqueHumidite(series, { seuil = 85, min = 60, max = 100 } = {}) {
  const valides = (series ?? []).filter((s) => Array.isArray(s.points) && s.points.length > 0);
  if (valides.length === 0) {
    return '<p class="sub">Aucune mesure sur la fenêtre demandée.</p>';
  }

  const largeur = 520;
  const hauteur = 210;
  const gauche = 40;
  const droite = 14;
  const haut = 12;
  const bas = 26;
  const longueur = Math.max(...valides.map((s) => s.points.length));
  const pasX = longueur > 1 ? (largeur - gauche - droite) / (longueur - 1) : 0;
  const x = (i) => gauche + i * pasX;
  const y = (v) => hauteur - bas - ((Math.min(max, Math.max(min, v)) - min) / (max - min)) * (hauteur - haut - bas);

  let svg = `<svg viewBox="0 0 ${largeur} ${hauteur}" role="img" aria-label="Évolution de l'humidité de l'air sur ${FENETRE_JOURS} jours pour ${valides.length} parcelle(s), seuil d'alerte à ${seuil} pour cent.">`;

  // Grille et graduations
  for (let i = 0; i <= 4; i += 1) {
    const valeur = min + (i * (max - min)) / 4;
    svg += `<line x1="${gauche}" x2="${largeur - droite}" y1="${y(valeur)}" y2="${y(valeur)}" stroke="var(--bord)"/>`;
    svg += `<text x="4" y="${y(valeur) + 3}">${Math.round(valeur)} %</text>`;
  }

  // Seuil d'alerte (RM1)
  svg += `<line x1="${gauche}" x2="${largeur - droite}" y1="${y(seuil)}" y2="${y(seuil)}" stroke="var(--ko)" stroke-dasharray="5 4"/>`;
  svg += `<text x="${largeur - 96}" y="${y(seuil) - 5}" style="fill:var(--ko)">Seuil ${seuil} %</text>`;

  // Courbes
  for (const serie of valides) {
    const couleur = serie.under_alert ? "var(--brun)" : "var(--ok)";
    const points = serie.points.map((p, i) => `${x(i)},${y(p.air_humidity_pct)}`).join(" ");
    svg += `<polyline fill="none" stroke="${couleur}" stroke-width="2.6" stroke-linejoin="round" points="${points}"/>`;
  }

  // Étiquettes de dates : une sur deux si la fenêtre est longue
  const reference = valides.reduce((a, b) => (b.points.length > a.points.length ? b : a));
  reference.points.forEach((point, i) => {
    if (longueur > 8 && i % 2 === 1) return;
    svg += `<text x="${x(i) - 12}" y="${hauteur - 8}">${jourCourt(point.date)}</text>`;
  });

  svg += "</svg>";
  return svg;
}

/** Tableau alternatif du graphique, pour les lecteurs d'écran. */
function tableauHumidite(series) {
  const lignes = (series ?? []).flatMap((serie) =>
    (serie.points ?? []).map(
      (point) =>
        `<tr><td>${esc(jourCourt(point.date))}</td><td>${esc(serie.plot_name)}</td><td>${nombre(point.air_humidity_pct)} %</td></tr>`,
    ),
  );
  if (lignes.length === 0) return "";
  return `<details class="donnees"><summary>Voir les données du graphique</summary>
    <div class="scroll"><table>
      <thead><tr><th>Jour</th><th>Parcelle</th><th>Humidité de l'air</th></tr></thead>
      <tbody>${lignes.join("")}</tbody>
    </table></div>
  </details>`;
}

/** Tableau alternatif de la courbe de prix, pour les lecteurs d'écran. */
function tableauPrix(prix) {
  const points = prix.points ?? [];
  if (points.length === 0) return "";
  const lignes = points
    .map(
      (point) =>
        `<tr><td>${esc(jourCourt(point.date))}</td><td>${nombre(point.reference_price, 0)}</td><td>${nombre(point.adjusted_price, 0)}</td></tr>`,
    )
    .join("");
  return `<details class="donnees"><summary>Voir les données de la courbe</summary>
    <div class="scroll"><table>
      <thead><tr><th>Jour</th><th>Prix de référence</th><th>Prix ajusté</th></tr></thead>
      <tbody>${lignes}</tbody>
    </table></div>
  </details>`;
}

/** Courbe de prix prédictive (contrat §4.5) en SVG accessible. */
function graphiquePrix(prix) {
  const points = prix.points ?? [];
  if (points.length === 0) {
    return '<p class="sub">Aucune donnée de prix sur la fenêtre demandée.</p>';
  }

  const largeur = 520;
  const hauteur = 210;
  const gauche = 54;
  const droite = 14;
  const haut = 12;
  const bas = 26;
  const valeurs = points.flatMap((p) => [Number(p.reference_price), Number(p.adjusted_price)]);
  const min = Math.floor(Math.min(...valeurs) / 50) * 50 - 25;
  const max = Math.ceil(Math.max(...valeurs) / 50) * 50 + 25;
  const pasX = points.length > 1 ? (largeur - gauche - droite) / (points.length - 1) : 0;
  const x = (i) => gauche + i * pasX;
  const y = (v) => hauteur - bas - ((v - min) / (max - min)) * (hauteur - haut - bas);
  const trace = (cle) => points.map((p, i) => `${x(i)},${y(Number(p[cle]))}`).join(" ");

  let svg = `<svg viewBox="0 0 ${largeur} ${hauteur}" role="img" aria-label="Prix du cacao sur ${points.length} jours, de ${nombre(min, 0)} à ${nombre(max, 0)} francs CFA par kilogramme.">`;

  for (let i = 0; i <= 4; i += 1) {
    const valeur = min + (i * (max - min)) / 4;
    svg += `<line x1="${gauche}" x2="${largeur - droite}" y1="${y(valeur)}" y2="${y(valeur)}" stroke="var(--bord)"/>`;
    svg += `<text x="4" y="${y(valeur) + 3}">${nombre(valeur, 0)}</text>`;
  }

  svg += `<polyline fill="none" stroke="var(--gris)" stroke-width="2" stroke-dasharray="5 4" points="${trace("reference_price")}"/>`;
  svg += `<polyline fill="none" stroke="var(--brun)" stroke-width="2.8" stroke-linejoin="round" points="${trace("adjusted_price")}"/>`;

  points.forEach((point, i) => {
    if (points.length > 8 && i % 2 === 1) return;
    svg += `<text x="${x(i) - 12}" y="${hauteur - 8}">${jourCourt(point.date)}</text>`;
  });

  svg += "</svg>";
  return svg;
}

/* ===== Vues ===== */

function vueTableauDeBord(donnees, prix) {
  const niveauGlobal = niveau(donnees.level);
  const delta = Number(donnees.humidity_delta_7d) || 0;
  const signe = delta > 0 ? "+" : "";
  const series = donnees.humidity_series ?? [];

  return `
  <div class="grille g4">
    <article class="card kpi">
      <div class="ic" aria-hidden="true"><span class="ms">bug_report</span></div>
      <div>
        <small>Indice d'Infestation Global</small>
        <b>${nombre(donnees.global_infestation_index, 0)}<span style="font-size:15px">/100</span></b>
        <span class="pill ${niveauGlobal.classe}">${niveauGlobal.libelle}</span>
      </div>
    </article>

    <article class="card kpi">
      <div class="ic" aria-hidden="true"><span class="ms">water_drop</span></div>
      <div>
        <small>Humidité moyenne (air)</small>
        <b>${nombre(donnees.avg_air_humidity_pct)} %</b>
        <small>${signe}${nombre(delta)} pts sur ${FENETRE_JOURS} jours</small>
      </div>
    </article>

    <article class="card kpi">
      <div class="ic" aria-hidden="true"><span class="ms">notifications_active</span></div>
      <div>
        <small>Alertes actives</small>
        <b>${nombre(donnees.active_alerts, 0)}</b>
        <small>humidité &gt; 85 % pendant 48 h</small>
      </div>
    </article>

    <article class="card kpi">
      <div class="ic" aria-hidden="true"><span class="ms">inventory_2</span></div>
      <div>
        <small>Volume sain estimé</small>
        <b>${nombre(donnees.estimated_healthy_volume_pct, 0)} %</b>
        <small>horizon ${FENETRE_JOURS} jours</small>
      </div>
    </article>
  </div>

  <div class="grille g2">
    <figure class="card graphique">
      <h3>Évolution de l'humidité de l'air</h3>
      <div class="sub">Parcelle en alerte (brun) et parcelle saine (vert), ${FENETRE_JOURS} jours</div>
      ${graphiqueHumidite(series)}
      <div class="legende">
        <span><i style="background:var(--brun)"></i>Parcelle en alerte</span>
        <span><i style="background:var(--ok)"></i>Parcelle saine</span>
        <span><i style="background:var(--ko)"></i>Seuil 85 %</span>
      </div>
      ${tableauHumidite(series)}
    </figure>

    <section class="card" aria-labelledby="titre-suivi">
      <h3 id="titre-suivi">Parcelles suivies</h3>
      <div class="sub">${nombre(donnees.plots_monitored, 0)} parcelles, fenêtre de ${FENETRE_JOURS} jours</div>
      <ul style="list-style:none;display:grid;gap:10px">
        ${series
          .map(
            (serie) => `<li style="display:flex;align-items:center;gap:10px">
              <span class="ms" aria-hidden="true" style="color:${serie.under_alert ? "var(--ko)" : "var(--ok)"}">${serie.under_alert ? "error" : "check_circle"}</span>
              <span style="flex:1">${esc(serie.plot_name)}</span>
              <span class="pill ${serie.under_alert ? "ko" : "ok"}">${serie.under_alert ? "Alerte" : "Sain"}</span>
            </li>`,
          )
          .join("")}
      </ul>
      <p class="sub" style="margin:14px 0 0">Calculé le <time datetime="${esc(donnees.generated_at)}">${esc(
        new Date(donnees.generated_at).toLocaleString("fr-FR"),
      )}</time></p>
    </section>
  </div>

  <figure class="card graphique graphique-prix">
    <h3>Courbe de prix prédictive</h3>
    <div class="sub">
      Prix de référence (pointillé) et prix ajusté par l'indice d'infestation (RM3), ${nombre(prix.horizon_days, 0)} jours, en ${esc(prix.unit ?? "FCFA/kg")}
      ${prix.is_demo ? '<span class="pill mod">Courbe de démonstration</span>' : ""}
    </div>
    ${graphiquePrix(prix)}
    <div class="legende">
      <span><i style="background:var(--gris)"></i>Prix de référence</span>
      <span><i style="background:var(--brun)"></i>Prix ajusté (RM3)</span>
      <span>Formule ${esc(prix.formula_version ?? "v1")}</span>
    </div>
    ${tableauPrix(prix)}
  </figure>`;
}

function vueProducteur(donnees) {
  const niveauGlobal = niveau(donnees.level);

  return `
  <div class="zt">
    <p class="sub">Une tâche en moins de 60 secondes (PB-15)</p>
    <div class="feu" style="background:${niveauGlobal.couleur}" role="img" aria-label="Niveau d'alerte : ${niveauGlobal.libelle}">
      <span class="ms" aria-hidden="true">${niveauGlobal.icone}</span>
    </div>

    <div class="gros">
      <button type="button" data-action="humidite" aria-label="Humidité de l'air : ${nombre(donnees.avg_air_humidity_pct)} pour cent">
        <span class="ms" aria-hidden="true">water_drop</span>
        <b>${nombre(donnees.avg_air_humidity_pct, 0)} %</b>
      </button>
      <button type="button" data-action="alertes" aria-label="Alertes actives : ${nombre(donnees.active_alerts, 0)}">
        <span class="ms" aria-hidden="true">notifications_active</span>
        <b>${nombre(donnees.active_alerts, 0)}</b>
      </button>
      <button type="button" data-action="ecouter" aria-label="Écouter l'alerte">
        <span class="ms" aria-hidden="true">volume_up</span>
        <b>Écouter</b>
      </button>
      <button type="button" data-action="appeler" aria-label="Appeler le conseiller agricole">
        <span class="ms" aria-hidden="true">call</span>
        <b>Appeler</b>
      </button>
    </div>
  </div>`;
}

/* ===== Interactions ===== */

const TITRES = { dash: "Tableau de bord", prod: "Vue producteur" };

function toast(message) {
  const zone = $("#toast");
  const element = document.createElement("div");
  element.className = "t";
  element.innerHTML = `<span class="ms" aria-hidden="true">check_circle</span><span>${esc(message)}</span>`;
  zone.append(element);
  setTimeout(() => element.remove(), 3200);
}

function afficherSource(source, motif) {
  const etat = $("#etat-source");
  etat.dataset.source = source;
  if (source === "api") {
    etat.textContent = "Données de l'API";
    etat.title = "Les indicateurs viennent de GET /api/v1/kpis.";
  } else {
    etat.textContent = "Données de démonstration";
    etat.title = `Repli sur le jeu de démonstration${motif ? ` (${motif})` : ""}.`;
  }
}

function appliquerTheme(theme) {
  const racine = document.documentElement;
  if (theme === "dark" || theme === "light") {
    racine.dataset.theme = theme;
  } else {
    delete racine.dataset.theme;
  }
  const bouton = $("#theme");
  const sombre =
    racine.dataset.theme === "dark" ||
    (!racine.dataset.theme && window.matchMedia("(prefers-color-scheme: dark)").matches);
  bouton.setAttribute("aria-pressed", String(sombre));
  bouton.setAttribute("aria-label", sombre ? "Passer au thème clair" : "Passer au thème sombre");
}

function basculerTheme() {
  const racine = document.documentElement;
  const sombre =
    racine.dataset.theme === "dark" ||
    (!racine.dataset.theme && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const suivant = sombre ? "light" : "dark";
  localStorage.setItem(THEME_KEY, suivant);
  appliquerTheme(suivant);
}

let kpisCourants = KPIS_DEMO;
let prixCourants = PRIX_DEMO;

function afficherVue(vue) {
  document.querySelectorAll("#nav button").forEach((bouton) => {
    if (bouton.dataset.vue === vue) {
      bouton.setAttribute("aria-current", "page");
    } else {
      bouton.removeAttribute("aria-current");
    }
  });
  $("#titre").textContent = TITRES[vue] ?? TITRES.dash;

  const zone = $("#vue");
  zone.innerHTML = vue === "prod" ? vueProducteur(kpisCourants) : vueTableauDeBord(kpisCourants, prixCourants);
  zone.focus({ preventScroll: true });
}

function cablerActions() {
  $("#nav").addEventListener("click", (evenement) => {
    const bouton = evenement.target.closest("button[data-vue]");
    if (bouton) afficherVue(bouton.dataset.vue);
  });

  $("#theme").addEventListener("click", basculerTheme);

  $("#vue").addEventListener("click", (evenement) => {
    const bouton = evenement.target.closest("button[data-action]");
    if (!bouton) return;
    const actions = {
      humidite: "Humidité de l'air : mesure la plus récente",
      alertes: "Parcelles en alerte : humidité au-dessus de 85 % pendant 48 h",
      ecouter: "Lecture vocale de l'alerte (simulation)",
      appeler: "Appel du conseiller agricole (simulation)",
    };
    toast(actions[bouton.dataset.action] ?? "Action");
  });

  $("#actualiser").addEventListener("click", async () => {
    $("#actualiser").disabled = true;
    await demarrer();
    $("#actualiser").disabled = false;
  });
}

async function demarrer() {
  const [{ donnees, source, motif }, prix] = await Promise.all([chargerKpis(), chargerPrix()]);
  kpisCourants = donnees;
  prixCourants = prix.donnees;
  afficherSource(source, motif);
  const vue = document.querySelector("#nav button[aria-current='page']")?.dataset.vue ?? "dash";
  afficherVue(vue);
}

document.addEventListener("DOMContentLoaded", () => {
  appliquerTheme(localStorage.getItem(THEME_KEY));
  cablerActions();
  demarrer();
});
