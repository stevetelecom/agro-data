// AGRO-DATA — Noeud d'acquisition ESP32-CAM
// Role : mesurer temperature et humidite (air + sol), capturer une image,
//        l'analyser grossierement, puis envoyer la mesure au backend.
//        Hors ligne, la mesure est ecrite sur la carte MicroSD et renvoyee
//        au retour du reseau (Store-and-Forward, BNF1/BNF8).
// Auteur : NTEINTIE Mounpain (MOD-C3) — implementation reprise par
//          MEKONTSO Olivier Steve (SM) apres l'absence de livraison du bloc C.
//
// Reference : docs/CONTRAT_JSON.md section 3 (message d'ingestion).
// ATTENTION : ce croquis n'a pas ete compile ni execute faute de materiel.
// Il decrit le comportement attendu ; les sorties reelles du boitier doivent
// etre relevees avant toute affirmation dans le dossier final.

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <SD_MMC.h>
#include <time.h>
#include "esp_camera.h"

// --------------------------------------------------------------------------
// Broches et constantes materielles
// --------------------------------------------------------------------------
#define DHT_PIN        13
#define DHT_TYPE       DHT22
#define SOIL_PIN       14          // capteur capacitif d'humidite du sol

#define SD_CLK         14          // remplacer par le cablage reel du boitier
#define SD_CMD         15
#define SD_D0          2

static const char *WIFI_SSID     = "AGRO-DATA-TERRAIN";
static const char *WIFI_PASSWORD = "a-changer-avant-mise-en-service";
static const char *API_URL       = "http://192.168.1.10:8000/api/v1/measurements";
static const char *API_KEY       = "agro-device-demo-key";
static const char *DEVICE_ID     = "AMB-P001";
static const char *GEO_ENC       = "lat:2.383,lon:11.283";

static const unsigned long MESURE_INTERVALLE_MS = 60UL * 60UL * 1000UL; // 1 h
static const char *TAMPON_PATH = "/buffer.jsonl";
static const uint32_t DELAI_HTTP_MS = 10000;

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long dernierEnvoi = 0;

// --------------------------------------------------------------------------
// Utilitaires
// --------------------------------------------------------------------------
/** Horodatage Unix en secondes, 0 si l'heure NTP n'est pas encore connue. */
uint32_t maintenant() {
  time_t t = time(nullptr);
  return (t > 1700000000) ? (uint32_t)t : 0;
}

/** Lit un capteur et borne la valeur dans la plage du contrat. */
float borner(float valeur, float min, float max, float defaut) {
  if (isnan(valeur)) return defaut;
  return constrain(valeur, min, max);
}

/** Lit l'humidite du sol (0-100 %) : le capteur capacitif renvoie 0-4095. */
float humiditeSol() {
  int brut = analogRead(SOIL_PIN);
  return constrain(map(brut, 2600, 900, 0, 100), 0, 100);
}

/** Taux de pixels sombres : approximation locale en attendant le modele IA. */
int diagnosticLocal(float *confiance) {
  camera_fb_t *image = esp_camera_fb_get();
  if (image == nullptr) {
    *confiance = 0.5f;
    return 0;
  }
  uint32_t sombres = 0;
  const uint32_t pixels = image->len / 3;
  for (uint32_t i = 0; i + 2 < image->len; i += 3 * 16) {
    if (image->buf[i] + image->buf[i + 1] + image->buf[i + 2] < 180) sombres++;
  }
  esp_camera_fb_return(image);
  const float ratio = pixels == 0 ? 0.0f : (float)sombres / (float)(pixels / 16);
  *confiance = constrain(0.55f + ratio, 0.5f, 0.99f);
  return (ratio > 0.25f) ? 1 : 0;
}

/** Construit le message JSON du contrat, sans champ supplementaire. */
String construireJson(uint32_t horodatage, float temperature, float humiditeAir,
                      float humiditeS, int detecte, float confiance) {
  String json = "{";
  json += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  json += "\"timestamp\":" + String(horodatage) + ",";
  json += "\"climate\":{\"temperature_c\":" + String(temperature, 1) + ",";
  json += "\"air_humidity_pct\":" + String(humiditeAir, 1) + ",";
  json += "\"soil_humidity_pct\":" + String(humiditeS, 1) + "},";
  json += "\"diagnostic_ia\":{\"phytophthora_detected\":" + String(detecte) + ",";
  json += "\"confidence\":" + String(confiance, 2) + "},";
  json += "\"geo_enc\":\"" + String(GEO_ENC) + "\"}";
  return json;
}

// --------------------------------------------------------------------------
// Store-and-Forward
// --------------------------------------------------------------------------
/** Ajoute une mesure au tampon MicroSD, une par ligne. */
bool mettreEnTampon(const String &json) {
  File fichier = SD_MMC.open(TAMPON_PATH, FILE_APPEND);
  if (!fichier) {
    Serial.println("MicroSD indisponible : mesure perdue");
    return false;
  }
  fichier.println(json);
  fichier.close();
  return true;
}

/** Envoie une mesure ; renvoie le code HTTP, -1 si le reseau est coupe. */
int envoyer(const String &json) {
  if (WiFi.status() != WL_CONNECTED) return -1;
  HTTPClient http;
  http.begin(API_URL);
  http.setTimeout(DELAI_HTTP_MS);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  const int code = http.POST(json);
  http.end();
  return code;
}

/**
 * Renvoie le tampon dans l'ordre.
 * 2xx et 422 (doublon ou mesure invalide) retirent la ligne : renvoyer la
 * meme mesure ne changerait rien. Tout autre code arrete la reprise.
 */
void viderTampon() {
  if (!SD_MMC.exists(TAMPON_PATH)) return;
  File lecture = SD_MMC.open(TAMPON_PATH, FILE_READ);
  if (!lecture) return;

  File restant = SD_MMC.open("/buffer.tmp", FILE_WRITE);
  uint16_t envoyees = 0, conservees = 0;

  while (lecture.available()) {
    String ligne = lecture.readStringUntil('\n');
    ligne.trim();
    if (ligne.length() == 0) continue;

    const int code = envoyer(ligne);
    const bool traitee = (code >= 200 && code < 300) || code == 422;
    if (traitee) {
      envoyees++;
    } else {
      restant.println(ligne);
      conservees++;
      if (code == -1) {
        Serial.println("Reseau perdu pendant la reprise, tampon conserve");
        break;
      }
    }
  }

  while (lecture.available()) {          // echec au milieu : garder la suite
    String ligne = lecture.readStringUntil('\n');
    if (ligne.length() > 0) {
      restant.println(ligne);
      conservees++;
    }
  }

  lecture.close();
  restant.close();
  SD_MMC.remove(TAMPON_PATH);
  if (conservees > 0) SD_MMC.rename("/buffer.tmp", TAMPON_PATH);
  else SD_MMC.remove("/buffer.tmp");

  Serial.printf("Reprise : %u envoyees, %u en attente\n", envoyees, conservees);
}

// --------------------------------------------------------------------------
// Cycle de vie
// --------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  dht.begin();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;  config.pin_d1 = 18; config.pin_d2 = 19; config.pin_d3 = 21;
  config.pin_d4 = 36; config.pin_d5 = 39; config.pin_d6 = 34; config.pin_d7 = 35;
  config.pin_xclk = 0; config.pin_pclk = 22; config.pin_vsync = 25;
  config.pin_href = 23; config.pin_sscb_sda = 26; config.pin_sscb_scl = 27;
  config.pin_pwdn = 32; config.pin_reset = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_RGB565;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;
  if (esp_camera_init(&config) != ESP_OK) Serial.println("Camera indisponible");

  SD_MMC.setPins(SD_CLK, SD_CMD, SD_D0);
  if (!SD_MMC.begin("/sdcard", true)) Serial.println("MicroSD indisponible");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  configTime(0, 0, "pool.ntp.org", "time.google.com");   // UTC, contrat section 3
  Serial.println("AGRO-DATA : noeud pret");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    viderTampon();
  }

  if (millis() - dernierEnvoi < MESURE_INTERVALLE_MS) {
    delay(1000);
    return;
  }
  dernierEnvoi = millis();

  const uint32_t horodatage = maintenant();
  if (horodatage == 0) {
    Serial.println("Heure NTP inconnue : mesure differee");
    return;
  }

  float confiance = 0.0f;
  const int detecte = diagnosticLocal(&confiance);
  const String json = construireJson(
      horodatage,
      borner(dht.readTemperature(), -10.0f, 55.0f, 27.0f),
      borner(dht.readHumidity(), 0.0f, 100.0f, 75.0f),
      humiditeSol(),
      detecte,
      confiance);

  const int code = envoyer(json);
  if (code >= 200 && code < 300) {
    Serial.printf("Mesure envoyee (%d)\n", code);
  } else if (code == 422) {
    Serial.println("Mesure refusee par le serveur : verifier le contrat");
  } else {
    Serial.printf("Envoi impossible (%d) : mise en tampon\n", code);
    mettreEnTampon(json);
  }
}
