/* Spots am oberen Comer See und Messstationen (ARPA Lombardia).
   Spot-Koordinaten liegen auf dem Wasser vor dem Spot (wie in training/sar_lake.py). */
const SPOTS = [
  { id: "colico",       name: "Colico",            short: "Colico",  lat: 46.137, lon: 9.372, shore: "east shore, northern basin" },
  { id: "gera_lario",   name: "Gera Lario",        short: "Gera",    lat: 46.168, lon: 9.372, shore: "northern end" },
  { id: "sorico_punta", name: "Sorico / La Punta", short: "Sorico",  lat: 46.162, lon: 9.392, shore: "northern end, Mera mouth" },
  { id: "domaso",       name: "Domaso",            short: "Domaso",  lat: 46.150, lon: 9.335, shore: "west shore" },
  { id: "dervio",       name: "Dervio",            short: "Dervio",  lat: 46.077, lon: 9.300, shore: "east shore, mid-lake" },
  { id: "cremia",       name: "Cremia",            short: "Cremia",  lat: 46.087, lon: 9.276, shore: "west shore, mid-lake" }
];

/* ARPA-Stationen: Sensor-IDs Windgeschwindigkeit/-richtung (training/download_arpa.py, data/arpa/sensors.json).
   sektor = Richtung, aus der der Breva an der Station ankommt (training/station_detail.py) */
const STATIONS = [
  { id: "samolaco", name: "Samolaco",  note: "Pian di Spagna, 206 m", lat: 46.2361, lon: 9.4267, speed: 11737, dir: 2117,  sektor: [112, 202] },
  { id: "colico",   name: "Colico",    note: "La Madoneta, 229 m",    lat: 46.1381, lon: 9.3847, speed: 19109, dir: 6008,  sektor: [225, 315] },
  { id: "morbegno", name: "Morbegno",  note: "Valtellina, 230 m",        lat: 46.1366, lon: 9.5843, speed: 19382, dir: 19383, sektor: [200, 290] },
  { id: "vercana",  name: "Vercana",   note: "above Domaso, 980 m",    lat: 46.1819, lon: 9.3247, speed: 11811, dir: 9077,  sektor: [180, 270] },
  { id: "sansiro",  name: "San Siro",  note: "Alpe Rescascìa, 1285 m", lat: 46.0719, lon: 9.2383, speed: 14715, dir: 14714, sektor: [180, 270] }
];

/* Punkte für die Breva-Zeichen aus den Wettermodellen */
const POINTS = [
  { id: "see",       lat: 46.07, lon: 9.29 },   // oberer See
  { id: "milano",    lat: 45.46, lon: 9.19 },   // Po-Ebene
  { id: "chiavenna", lat: 46.32, lon: 9.40 },   // Tal im Norden
  { id: "zurich",    lat: 47.38, lon: 8.54 }    // Alpennordseite (Föhn)
];

const THRESHOLDS = [14];          // Breva-Tag: ≥ 14 kn für mind. 2 h (Samolaco oder Colico, Satellitenfaktor)
const SEASON = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];   // ganzes Jahr

/* Punkte des Breva-Modells (wie training/breva_daten.py POINTS) – Vorhersage ECMWF, 31 Tage zurück für Vortag/30-Tage-Mittel */
const MODEL_POINTS = {
  milano: [45.46, 9.19], bergamo: [45.70, 9.67], see: [46.07, 9.29], chiavenna: [46.32, 9.40], sondrio: [46.17, 9.87],
  engadin: [46.50, 9.84], zurich: [47.38, 8.54], muenchen: [48.14, 11.58], genova: [44.41, 8.93], venezia: [45.44, 12.33],
  lyon: [45.76, 4.84]
};
const MODEL_VARS = ["temperature_2m", "dew_point_2m", "pressure_msl", "shortwave_radiation", "cloud_cover", "precipitation",
  "wind_speed_10m", "wind_direction_10m"];
