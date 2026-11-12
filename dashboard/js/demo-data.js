/**
 * Rôle : jeu de mesures de démonstration, mêmes scénarios que le bloc C
 *        (parcelle saine, humidité critique, cas intermédiaire).
 * Auteur : NEGOUE Patrick
 * Bloc : B
 */

const STORAGE_KEY = "agro_demo_db_v1";

function unit(seed) {
  const value = Math.sin(seed) * 10000;
  return value - Math.floor(value);
}

function round1(value) {
  return Math.round(value * 10) / 10;
}

function round2(value) {
  return Math.round(value * 100) / 100;
}

function climateFor(profile, timestamp, hoursAgo) {
  const noise = unit(timestamp);
  if (profile === "critical") {
    const wet = hoursAgo < 60;
    return {
      temperature_c: round1(25 + noise * 3.5),
      air_humidity_pct: round1(wet ? 86 + noise * 7 : 72 + noise * 4),
      soil_humidity_pct: round1(wet ? 68 + noise * 12 : 55 + noise * 8),
    };
  }
  if (profile === "healthy") {
    return {
      temperature_c: round1(26 + noise * 3),
      air_humidity_pct: round1(63 + noise * 9),
      soil_humidity_pct: round1(48 + noise * 10),
    };
  }
  const wet = hoursAgo < 30;
  return {
    temperature_c: round1(25.5 + noise * 3),
    air_humidity_pct: round1(wet ? 86 + noise * 4 : 74 + noise * 6),
    soil_humidity_pct: round1(58 + noise * 10),
  };
}

function diagnosticFor(profile, timestamp, hoursAgo) {
  const noise = unit(timestamp + 17);
  if (profile === "critical" && hoursAgo < 60 && noise < 0.45) {
    return { phytophthora_detected: 1, confidence: round2(0.72 + unit(timestamp + 3) * 0.24) };
  }
  if (profile === "mixed" && hoursAgo < 30 && noise < 0.12) {
    return { phytophthora_detected: 1, confidence: round2(0.6 + unit(timestamp + 5) * 0.3) };
  }
  return { phytophthora_detected: 0, confidence: round2(0.88 + unit(timestamp + 9) * 0.1) };
}

export function createSeed() {
  const end = new Date();
  end.setMinutes(0, 0, 0);
  const endSec = Math.floor(end.getTime() / 1000);
  const plots = [
    {
      id: "p1",
      name: "Parcelle Nord",
      sector: "Ambam Nord",
      village: "Ambam",
      surface_ha: 1.5,
      device_id: "AMB-P001",
      reference_volume_kg: 1200,
      profile: "critical",
    },
    {
      id: "p2",
      name: "Parcelle Fleuve",
      sector: "Ambam Fleuve",
      village: "Ambam",
      surface_ha: 1.1,
      device_id: "AMB-P002",
      reference_volume_kg: 900,
      profile: "healthy",
    },
    {
      id: "p3",
      name: "Parcelle Est",
      sector: "Ambam Est",
      village: "Ebolowa",
      surface_ha: 0.9,
      device_id: "AMB-P003",
      reference_volume_kg: 750,
      profile: "mixed",
    },
  ];
  const devices = plots.map((plot, index) => ({
    id: `d${index + 1}`,
    device_id: plot.device_id,
    plot_id: plot.id,
    status: "actif",
  }));
  const subscribers = [
    { id: "s1", name: "Administration", email: "acheteur@ebolowa.cm", role: "admin", plan: "Exploitation" },
    { id: "s2", name: "Acheteur Ebolowa", email: "acheteur@agrodata.local", role: "acheteur", plan: "Marché" },
  ];
  const measurements = [];
  plots.forEach((plot) => {
    for (let hoursAgo = 71; hoursAgo >= 0; hoursAgo -= 1) {
      const timestamp = endSec - hoursAgo * 3600;
      measurements.push({
        id: `${plot.device_id}-${timestamp}`,
        device_id: plot.device_id,
        timestamp,
        climate: climateFor(plot.profile, timestamp, hoursAgo),
        diagnostic_ia: diagnosticFor(plot.profile, timestamp, hoursAgo),
        geo_enc: "NON-CHIFFRE-DEMO",
      });
    }
  });
  return { version: 1, plots, devices, subscribers, measurements };
}

export function loadDemoDb() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed?.version === 1 && Array.isArray(parsed.plots) && Array.isArray(parsed.measurements)) {
        return parsed;
      }
    }
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
  const seeded = createSeed();
  saveDemoDb(seeded);
  return seeded;
}

export function saveDemoDb(db) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(db));
}

export function resetDemoDb() {
  localStorage.removeItem(STORAGE_KEY);
  return loadDemoDb();
}
