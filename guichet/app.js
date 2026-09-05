/*
 * Poste guichet SentinelleCoop.
 *
 * Le filtrage nominal (M1/M2) tourne entierement cote client, en temps reel
 * pendant la saisie (Art. 20 du TDR — aucune action a lancer), a partir du
 * meme referentiel et du meme algorithme que le moteur Python (moteur.js,
 * portage documente de phonetics.py/matcher.py).
 *
 * Les verdicts LBC/FT (M3/M4) sont precalcules par verdicts.py et charges
 * depuis data/verdicts_demo.json : ils dependent d'un historique de
 * transactions horodatees, pas d'une saisie au guichet, donc rien a
 * recalculer en direct ici — seulement a afficher.
 */

(function () {
  "use strict";

  const state = {
    data: null,
    index: null,
    alertes: [],
    journal: [],
    dernierFiltrage: null,
  };

  function escapeHTML(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function money(v) {
    return new Intl.NumberFormat("fr-FR").format(v) + " FCFA";
  }

  function horodatage() {
    return new Date().toLocaleString("fr-FR");
  }

  function ajouterJournal(texte) {
    state.journal.unshift({ horodatage: horodatage(), texte });
    renderJournal();
  }

  // ---- Chargement des donnees ----------------------------------------------

  async function charger() {
    const reponse = await fetch("../data/verdicts_demo.json");
    if (!reponse.ok) throw new Error(`HTTP ${reponse.status}`);
    state.data = await reponse.json();
    state.index = new Index(state.data.referentiel);

    for (const client of state.data.clients) {
      for (const v of client.verdicts_lbc_ft) {
        state.alertes.push({
          id: `${client.id}-${state.alertes.length}`,
          client,
          categorie: v.categorie,
          severite: v.severite,
          motif: v.motif,
          statut: "a_revoir",
        });
      }
    }

    renderStatus();
    renderAudit();
    renderTransactions();
    renderAlertes();
    ajouterJournal("Référentiel chargé, portefeuille analysé.");
  }

  // ---- Statut / audit --------------------------------------------------------

  function renderStatus() {
    const genere = state.data.genere_le;
    let texte = "date inconnue";
    if (genere) {
      const dt = new Date(genere);
      const heures = (Date.now() - dt.getTime()) / 3_600_000;
      texte = heures < 48 && heures >= 0
        ? `synchronisé il y a ${heures.toFixed(1)} h`
        : `synchronisé le ${dt.toLocaleDateString("fr-FR")}`;
    }
    document.querySelector("#statusFraicheur").textContent = texte;
  }

  function renderAudit() {
    document.querySelector("#auditListe").textContent =
      `${state.data.referentiel.length} entrées (ONU + démo)`;
    document.querySelector("#auditSeuilBloquant").textContent =
      state.data.seuils.bloquant.toFixed(2);
    document.querySelector("#auditSeuilInformatif").textContent =
      state.data.seuils.informatif.toFixed(2);
    renderJournal();
  }

  function renderJournal() {
    const ol = document.querySelector("#auditJournal");
    if (!state.journal.length) {
      ol.innerHTML = "<li>Aucune entrée.</li>";
      return;
    }
    ol.innerHTML = state.journal
      .map((e) => `<li><time>${escapeHTML(e.horodatage)}</time>${escapeHTML(e.texte)}</li>`)
      .join("");
  }

  // ---- Filtrage en temps reel -------------------------------------------------

  function verdictNiveau(score) {
    if (score >= state.data.seuils.bloquant) return "BLOQUANT";
    if (score >= state.data.seuils.informatif) return "INFORMATIF";
    return "SOUS_SEUIL";
  }

  function trouverPPE(nom) {
    const cible = nom.trim().toLowerCase();
    return (
      state.data.ppe.find((p) =>
        [p.nom, ...p.alias].some((c) => c.trim().toLowerCase() === cible)
      ) || null
    );
  }

  let debounce = null;
  function surSaisieNom(evt) {
    clearTimeout(debounce);
    const valeur = evt.target.value;
    debounce = setTimeout(() => filtrerEnDirect(valeur), 200);
  }

  function filtrerEnDirect(nomBrut) {
    const zone = document.querySelector("#resultatFiltrage");
    const nom = nomBrut.trim();
    if (nom.length < 2) {
      zone.innerHTML = '<p class="etat-vide">En attente de saisie…</p>';
      return;
    }

    const correspondances = state.index.filtrer(nom, state.data.seuils.informatif, 3);
    const meilleure = correspondances[0] || null;
    const ppe = trouverPPE(nom);
    const niveau = meilleure ? verdictNiveau(meilleure.score) : "SOUS_SEUIL";

    zone.innerHTML = rendreResultat(nom, meilleure, niveau, ppe);

    const cle = `${nom.toLowerCase()}|${niveau}|${ppe ? ppe.id : ""}`;
    if ((niveau !== "SOUS_SEUIL" || ppe) && state.dernierFiltrage !== cle) {
      state.dernierFiltrage = cle;

      if (niveau !== "SOUS_SEUIL") {
        state.alertes.unshift({
          id: `filtrage-${Date.now()}`,
          client: { id: "-", nom },
          categorie: "FILTRAGE",
          severite: niveau,
          motif: `Rapprochement avec « ${meilleure.nom_liste} » (${meilleure.liste}, score ${meilleure.score.toFixed(4)})`
            + (meilleure.via_alias ? ` via l'alias « ${meilleure.via_alias} »` : ""),
          statut: "a_revoir",
        });
        ajouterJournal(`Filtrage ${niveau.toLowerCase()} — ${nom} (${meilleure.nom_liste}).`);
      }

      if (ppe) {
        state.alertes.unshift({
          id: `ppe-${Date.now()}`,
          client: { id: "-", nom },
          categorie: "PPE",
          severite: "INFORMATIF",
          motif: `Personne politiquement exposée depuis ${ppe.depuis} (${ppe.fonction})`
            + (ppe.en_retard ? " — réévaluation triennale en retard (art. 29)" : ""),
          statut: "a_revoir",
        });
        ajouterJournal(`PPE identifiée — ${nom}.`);
      }

      renderAlertes();
    }
  }

  function rendreResultat(nom, meilleure, niveau, ppe) {
    if (!meilleure && !ppe) {
      return `
        <span class="badge conforme">Aucun rapprochement</span>
        <p class="etat-vide">« ${escapeHTML(nom)} » ne correspond à aucune entrée du référentiel au seuil actuel.</p>
      `;
    }

    let sortie = "";
    if (meilleure) {
      const classe = niveau === "BLOQUANT" ? "bloquant" : "informatif";
      const label = niveau === "BLOQUANT" ? "Alerte bloquante" : "Alerte informative";
      sortie += `
        <span class="badge ${classe}">${label}</span>
        <h3 class="resultat-titre">${escapeHTML(meilleure.nom_liste)}</h3>
        <div class="barre-score">
          <div class="jauge"><span style="width:${Math.round(meilleure.score * 100)}%"></span></div>
          <strong>${(meilleure.score * 100).toFixed(1)}%</strong>
        </div>
        <ul class="motifs">
          <li>Source : ${escapeHTML(meilleure.liste)}${meilleure.reference ? " — " + escapeHTML(meilleure.reference) : ""}</li>
          ${meilleure.via_alias ? `<li>Rapproché via l'alias « ${escapeHTML(meilleure.via_alias)} »</li>` : ""}
          <li>Décision journalisée pour revue conformité.</li>
        </ul>
      `;
    } else {
      sortie += `<span class="badge conforme">Aucun rapprochement de sanction</span>`;
    }

    if (ppe) {
      sortie += `
        <span class="badge ppe">PPE — ${escapeHTML(ppe.fonction)}</span>
        <p class="motifs">Exposée depuis ${escapeHTML(ppe.depuis)}.${ppe.en_retard ? " Réévaluation triennale en retard (art. 29)." : ""}</p>
      `;
    }
    return sortie;
  }

  // ---- Transactions ---------------------------------------------------------

  function badgeVerdict(v) {
    const classe = v.severite === "BLOQUANT" ? "bloquant" : "informatif";
    const label = v.severite === "BLOQUANT" ? "bloquant" : "informatif";
    return `<span class="badge ${classe}">${escapeHTML(v.categorie)} · ${label}</span>`;
  }

  function renderTransactions() {
    const zone = document.querySelector("#cartesClients");
    zone.innerHTML = state.data.clients
      .map((client) => {
        const badges = client.verdicts_lbc_ft.length
          ? client.verdicts_lbc_ft.map(badgeVerdict).join("")
          : '<span class="badge conforme">Conforme</span>';
        const motifs = client.verdicts_lbc_ft
          .map((v) => `<li>${escapeHTML(v.motif)}</li>`)
          .join("");
        return `
          <article class="panel carte-client">
            <div class="view-header">
              <h3>${escapeHTML(client.nom)}</h3>
              ${client.ppe ? '<span class="badge ppe">PPE</span>' : ""}
            </div>
            <p class="sous-titre">${escapeHTML(client.id)} · ${escapeHTML(client.type)} · ${escapeHTML(client.agence)}</p>
            <ul class="liste-comptes">
              ${client.comptes.map((c) => `<li>${escapeHTML(c.id)} — ${money(c.solde)}</li>`).join("")}
            </ul>
            <div class="solde-consolide">${money(client.solde_consolide)} <span class="statut-tag">solde consolidé</span></div>
            <div class="badges-client">${badges}</div>
            ${motifs ? `<ul class="motifs">${motifs}</ul>` : ""}
          </article>
        `;
      })
      .join("");
  }

  // ---- Alertes ----------------------------------------------------------------

  const LIBELLE_STATUT = { a_revoir: "À revoir", confirmee: "Confirmée", levee: "Levée", escaladee: "Escaladée" };

  function renderAlertes() {
    const zone = document.querySelector("#listeAlertes");
    const compteur = document.querySelector("#compteurAlertes");
    compteur.hidden = state.alertes.length === 0;
    compteur.textContent = String(state.alertes.length);

    if (!state.alertes.length) {
      zone.innerHTML = '<p class="etat-vide-large">Aucune alerte en file.</p>';
      return;
    }

    zone.innerHTML = state.alertes
      .map((a) => {
        const classe = a.severite === "BLOQUANT" ? "bloquant" : "informatif";
        const label = a.severite === "BLOQUANT" ? "bloquant" : "informatif";
        return `
          <article class="panel alerte-carte" data-statut="${a.statut}">
            <div>
              <span class="badge ${classe}">${escapeHTML(a.categorie)} · ${label}</span>
              <h3>${escapeHTML(a.client.nom)}</h3>
              <p>${escapeHTML(a.motif)}</p>
              <p class="statut-tag">${LIBELLE_STATUT[a.statut]}</p>
            </div>
            <div class="alerte-actions">
              <button class="btn-secondaire" data-action="confirmee" data-id="${escapeHTML(a.id)}">Confirmer</button>
              <button class="btn-secondaire" data-action="levee" data-id="${escapeHTML(a.id)}">Lever</button>
              <button class="btn-secondaire" data-action="escaladee" data-id="${escapeHTML(a.id)}">Escalader</button>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function surActionAlerte(evt) {
    const bouton = evt.target.closest("button[data-action]");
    if (!bouton) return;
    const alerte = state.alertes.find((a) => a.id === bouton.dataset.id);
    if (!alerte) return;
    alerte.statut = bouton.dataset.action;
    renderAlertes();
    ajouterJournal(`${LIBELLE_STATUT[alerte.statut]} — ${alerte.client.nom} (${alerte.categorie}).`);
  }

  // ---- Rapport ------------------------------------------------------------------

  function genererRapport() {
    const principale = state.alertes.find((a) => a.severite === "BLOQUANT") || state.alertes[0];
    const lignes = [
      "RAPPORT CONFIDENTIEL — SENTINELLECOOP",
      `Horodatage : ${horodatage()}`,
      `Référentiel : ${state.data.referentiel.length} entrées, exécution locale`,
      principale
        ? `Alerte principale : ${principale.categorie} ${principale.severite} — ${principale.client.nom}`
        : "Alerte principale : aucune",
      principale ? `Motif : ${principale.motif}` : "Motif : sans objet",
      "Décision : à compléter par le responsable conformité",
      "Note : données clients simulées pour démonstration hackathon.",
    ];
    document.querySelector("#rapportBox").textContent = lignes.join("\n");
    ajouterJournal("Rapport généré.");
  }

  // ---- Navigation par onglets --------------------------------------------------

  function activerOnglet(vue) {
    for (const bouton of document.querySelectorAll(".tab")) {
      const actif = bouton.dataset.view === vue;
      bouton.classList.toggle("is-active", actif);
      bouton.setAttribute("aria-selected", String(actif));
      bouton.tabIndex = actif ? 0 : -1;
    }
    for (const panneau of document.querySelectorAll("main > section")) {
      panneau.hidden = panneau.id !== `panel-${vue}`;
    }
  }

  function surClicOnglet(evt) {
    const bouton = evt.target.closest(".tab");
    if (bouton) activerOnglet(bouton.dataset.view);
  }

  function surClavierOnglets(evt) {
    if (evt.key !== "ArrowRight" && evt.key !== "ArrowLeft") return;
    const onglets = [...document.querySelectorAll(".tab")];
    const courant = onglets.findIndex((b) => b.classList.contains("is-active"));
    if (courant === -1) return;
    const cible = evt.key === "ArrowRight"
      ? onglets[(courant + 1) % onglets.length]
      : onglets[(courant - 1 + onglets.length) % onglets.length];
    evt.preventDefault();
    cible.focus();
    activerOnglet(cible.dataset.view);
  }

  // ---- Initialisation -------------------------------------------------------------

  document.querySelector("#nomClient").addEventListener("input", surSaisieNom);
  document.querySelector(".tabs").addEventListener("click", surClicOnglet);
  document.querySelector(".tabs").addEventListener("keydown", surClavierOnglets);
  document.querySelector("#listeAlertes").addEventListener("click", surActionAlerte);
  document.querySelector("#genererRapport").addEventListener("click", genererRapport);

  charger().catch((err) => {
    document.querySelector("#resultatFiltrage").innerHTML =
      `<p class="etat-vide">Erreur de chargement du référentiel : ${escapeHTML(err.message)}</p>`;
  });
})();
