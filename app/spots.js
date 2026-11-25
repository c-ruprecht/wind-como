/* Spots am oberen Comer See und Messstationen (ARPA Lombardia).
   Spot-Koordinaten liegen auf dem Wasser vor dem Spot (wie in training/sar_lake.py). */
const SPOTS = [
  { id: "colico",       name: "Colico",            short: "Colico",  lat: 46.137, lon: 9.372, shore: "Ostufer, Nordbecken" },
  { id: "gera_lario",   name: "Gera Lario",        short: "Gera",    lat: 46.168, lon: 9.372, shore: "Nordende" },
  { id: "sorico_punta", name: "Sorico / La Punta", short: "Sorico",  lat: 46.162, lon: 9.392, shore: "Nordende, Mera-Mündung" },
  { id: "domaso",       name: "Domaso",            short: "Domaso",  lat: 46.150, lon: 9.335, shore: "Westufer" },
  { id: "dervio",       name: "Dervio",            short: "Dervio",  lat: 46.077, lon: 9.300, shore: "Ostufer, Seemitte" },
  { id: "cremia",       name: "Cremia",            short: "Cremia",  lat: 46.087, lon: 9.276, shore: "Westufer, Seemitte" }
];

/* ARPA-Stationen: Sensor-IDs Windgeschwindigkeit/-richtung (training/download_arpa.py, data/arpa/sensors.json).
   sektor = Richtung, aus der der Breva an der Station ankommt (training/station_detail.py) */
const STATIONS = [
  { id: "samolaco", name: "Samolaco",  note: "Pian di Spagna, 206 m", lat: 46.2361, lon: 9.4267, speed: 11737, dir: 2117,  sektor: [112, 202] },
  { id: "colico",   name: "Colico",    note: "La Madoneta, 229 m",    lat: 46.1381, lon: 9.3847, speed: 19109, dir: 6008,  sektor: [225, 315] },
  { id: "morbegno", name: "Morbegno",  note: "Veltlin, 230 m",        lat: 46.1366, lon: 9.5843, speed: 19382, dir: 19383, sektor: [200, 290] },
  { id: "vercana",  name: "Vercana",   note: "über Domaso, 980 m",    lat: 46.1819, lon: 9.3247, speed: 11811, dir: 9077,  sektor: [180, 270] },
  { id: "sansiro",  name: "San Siro",  note: "Alpe Rescascìa, 1285 m", lat: 46.0719, lon: 9.2383, speed: 14715, dir: 14714, sektor: [180, 270] }
];

/* Punkte für die Breva-Zeichen aus den Wettermodellen */
const POINTS = [
  { id: "see",       lat: 46.07, lon: 9.29 },   // oberer See
  { id: "milano",    lat: 45.46, lon: 9.19 },   // Po-Ebene
  { id: "chiavenna", lat: 46.32, lon: 9.40 },   // Tal im Norden
  { id: "zurich",    lat: 47.38, lon: 8.54 }    // Alpennordseite (Föhn)
];

const THRESHOLDS = [14, 18];
const SEASON = [4, 5, 6, 7, 8, 9];   // Breva-Saison, für die Klima und Satellit ausgewertet sind
