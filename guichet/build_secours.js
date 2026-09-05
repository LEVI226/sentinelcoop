// Regenere guichet/donnees_secours.js a partir de data/verdicts_demo.json.
//
// donnees_secours.js est la copie de secours embarquee que guichet/app.js
// charge quand aucun fetch() n'est possible (poste sans serveur local,
// page ouverte directement en file://, ou serveur en panne) — le mode
// degrade maximal decrit dans data/scenarios.md. Un <script src="...">
// classique fonctionne toujours en file://, contrairement a fetch().
//
// A relancer apres chaque regeneration de data/verdicts_demo.json :
//   python -m sentinellecoop.exporter_demo
//   node guichet/build_secours.js

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const source = join(__dirname, "..", "data", "verdicts_demo.json");
const cible = join(__dirname, "donnees_secours.js");

const donnees = JSON.parse(readFileSync(source, "utf-8"));

const entete = `// Fichier genere automatiquement par guichet/build_secours.js — ne pas
// editer a la main. Copie de secours de data/verdicts_demo.json, chargee par
// guichet/app.js uniquement quand fetch() echoue (mode degrade). Regenerer
// avec : node guichet/build_secours.js
`;

writeFileSync(
  cible,
  `${entete}\nwindow.DONNEES_SECOURS_SENTINELLECOOP = ${JSON.stringify(donnees)};\n`,
  "utf-8"
);

console.log(`${cible} ecrit (${donnees.clients.length} clients, ${donnees.referentiel.length} entrees referentiel).`);
