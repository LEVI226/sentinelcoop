// Verifie le portage JS (moteur.js) contre le jeu de 99 variantes attestees,
// en comparant directement aux resultats du moteur Python
// (data/variantes_noms_ao.csv + seuils de matcher.py). A relancer apres
// toute modification de moteur.js ou de phonetics.py/matcher.py, pour
// s'assurer que les deux restent en accord.
//
// Execution :  node guichet/moteur.test.mjs

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));
const code = readFileSync(join(__dirname, "moteur.js"), "utf-8");
const ctx = {};
vm.createContext(ctx);
vm.runInContext(code + "\nthis.similariteNom = similariteNom; this.PoidsJetons = PoidsJetons;", ctx);

const csv = readFileSync(join(__dirname, "..", "data", "variantes_noms_ao.csv"), "utf-8");
const lignes = csv.trim().split("\n").slice(1);
const paires = lignes.map((l) => l.split(","));

const referentiel = JSON.parse(readFileSync(join(__dirname, "..", "data", "verdicts_demo.json"), "utf-8")).referentiel;
const corpus = [];
for (const e of referentiel) {
  corpus.push(e.nom);
  for (const a of e.alias) corpus.push(a);
}
const poids = new ctx.PoidsJetons(corpus);

const SEUIL_INFORMATIF = 0.88;
let detectees = 0;
const manques = [];
for (const [ref, variante, cat] of paires) {
  const score = ctx.similariteNom(ref, variante, poids);
  if (score >= SEUIL_INFORMATIF) detectees++;
  else manques.push([ref, variante, cat, score.toFixed(3)]);
}
console.log(`Rappel JS (seuil 0.88) : ${detectees}/${paires.length} = ${(100 * detectees / paires.length).toFixed(1)}%`);
console.log(`Manques (${manques.length}) :`);
for (const m of manques) console.log("  ", m.join(" / "));

// Cas prioritaire de la demo (SPECS.md)
const casJury = ctx.similariteNom("Djallo Mamadou", "Diallo Mamadou", poids);
console.log(`\nCas jury Djallo/Diallo Mamadou : score ${casJury.toFixed(4)} (attendu >= 0.90)`);

// Le portage doit rester au moins aussi bon que le moteur Python mesure par
// benchmark.py (98.0% au seuil 0.88, cf. data/scenarios.md) : une regression
// ici signale un ecart entre moteur.js et phonetics.py/matcher.py.
const RAPPEL_MINIMUM = 0.97;
let echec = false;
if (detectees / paires.length < RAPPEL_MINIMUM) {
  console.error(`ECHEC : rappel sous le minimum attendu (${RAPPEL_MINIMUM * 100}%).`);
  echec = true;
}
if (casJury < 0.90) {
  console.error("ECHEC : le cas jury Djallo/Diallo Mamadou ne franchit plus le seuil bloquant.");
  echec = true;
}
process.exit(echec ? 1 : 0);
