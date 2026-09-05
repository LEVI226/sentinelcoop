const watchlist = [
  {
    id: "ONU-DEM-017",
    name: "Diallo Mamadou",
    aliases: ["Jallo Mamadu", "Djallo Mamadou", "Diallo Mamadu"],
    source: "ONU - donnees de demonstration",
    type: "Personne sanctionnee",
  },
  {
    id: "PPE-BF-044",
    name: "Ouedraogo Salif",
    aliases: ["Wedraogo Salif", "Ouédraogo Salifou"],
    source: "PPE interne - donnees de demonstration",
    type: "PPE",
  },
  {
    id: "ONU-DEM-061",
    name: "Mohamed Alhaji Cisse",
    aliases: ["Muhammad El Hadj Sisse", "Mahamadou Al Hadji Cise"],
    source: "ONU - donnees de demonstration",
    type: "Personne sous surveillance",
  },
];

const clients = [
  {
    id: "C-1029",
    name: "Diallo Mamadou",
    accounts: [
      { id: "001-771", balance: 860000 },
      { id: "014-219", balance: 410000 },
      { id: "031-554", balance: 230000 },
    ],
    transactions: [480000, 475000, 460000, 430000],
  },
  {
    id: "C-2214",
    name: "Awa Sawadogo",
    accounts: [{ id: "008-194", balance: 175000 }],
    transactions: [25000, 14000, 35000],
  },
  {
    id: "C-3091",
    name: "Ouedraogo Salif",
    accounts: [
      { id: "002-087", balance: 950000 },
      { id: "019-441", balance: 320000 },
    ],
    transactions: [800000, 350000, 210000],
  },
];

const state = {
  alerts: [],
  audit: [
    "08:02 - Correctif referentiel ONU applique localement",
    "08:05 - Session guichet ouverte en mode hors-ligne possible",
  ],
};

const equivalences = [
  [/dj/g, "j"],
  [/di(?=a|o)/g, "j"],
  [/ou/g, "w"],
  [/ph/g, "f"],
  [/kh/g, "h"],
  [/ck/g, "k"],
  [/[cq]/g, "k"],
  [/[çc]/g, "s"],
  [/ss/g, "s"],
  [/z/g, "s"],
  [/muh?amm?ad|mahamadou|mohamed/g, "mamadou"],
  [/alhaji|elhadj|el hadj|al hadji/g, "hadj"],
];

function normalizeName(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function phonetic(value) {
  let output = normalizeName(value);
  equivalences.forEach(([pattern, replacement]) => {
    output = output.replace(pattern, replacement);
  });
  return output;
}

function tokenSimilarity(a, b) {
  const left = new Set(phonetic(a).split(" ").filter(Boolean));
  const right = new Set(phonetic(b).split(" ").filter(Boolean));
  const intersection = [...left].filter((token) => right.has(token)).length;
  const union = new Set([...left, ...right]).size || 1;
  return intersection / union;
}

function screenClient(name) {
  const candidates = watchlist.flatMap((entry) => [entry.name, ...entry.aliases].map((alias) => ({ entry, alias })));
  const best = candidates
    .map((candidate) => ({ ...candidate, score: tokenSimilarity(name, candidate.alias) }))
    .sort((a, b) => b.score - a.score)[0];
  const score = Math.round(best.score * 100);
  const decision = score >= 90 ? "blocking" : score >= 75 ? "info" : "clear";
  return { ...best, score, decision };
}

function analyzeClient(client) {
  const accountTotal = client.accounts.reduce((sum, account) => sum + account.balance, 0);
  const sevenDayTotal = client.transactions.reduce((sum, amount) => sum + amount, 0);
  const splitCount = client.transactions.filter((amount) => amount < 500000).length;
  const fractioning = sevenDayTotal >= 1500000 && splitCount >= 3;
  const rebound = client.transactions.some((amount) => amount >= 750000) && client.accounts.length > 1;
  return {
    client,
    accountTotal,
    sevenDayTotal,
    signal: fractioning ? "Fractionnement" : rebound ? "Compte rebond" : "Conforme",
    severity: fractioning ? "stop" : rebound ? "warn" : "ok",
  };
}

function money(value) {
  return new Intl.NumberFormat("fr-FR").format(value) + " FCFA";
}

function escapeHTML(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function addAlert(alert) {
  const exists = state.alerts.some((item) => item.id === alert.id);
  if (!exists) state.alerts.unshift(alert);
}

function renderScreenResult(result) {
  const labels = {
    blocking: ["Alerte bloquante", "blocking"],
    info: ["Alerte informative", "info"],
    clear: ["Aucun blocage", "clear"],
  };
  const [label, className] = labels[result.decision];
  document.querySelector("#screenResult").innerHTML = `
    <span class="verdict ${className}">${label}</span>
    <h3 class="match-title">${result.entry.name}</h3>
    <div class="score-line">
      <div class="meter"><span style="width:${result.score}%"></span></div>
      <strong>${result.score}%</strong>
    </div>
    <ul class="reason-list">
      <li>Variante rapprochee: ${result.alias}</li>
      <li>Source: ${result.entry.source}</li>
      <li>Type: ${result.entry.type}</li>
      <li>Decision journalisee pour revue conformite.</li>
    </ul>
  `;
}

function renderTransactions() {
  const analyses = clients.map(analyzeClient);
  document.querySelector("#transactionRows").innerHTML = analyses
    .map((item) => `
      <tr>
        <td><strong>${item.client.name}</strong><br><span class="label">${item.client.id}</span></td>
        <td>${item.client.accounts.map((account) => account.id).join("<br>")}</td>
        <td>${money(item.accountTotal)}</td>
        <td>${money(item.sevenDayTotal)}</td>
        <td><span class="signal ${item.severity}">${item.signal}</span></td>
      </tr>
    `)
    .join("");

  analyses.filter((item) => item.severity !== "ok").forEach((item) => {
    addAlert({
      id: `TX-${item.client.id}`,
      severity: item.severity,
      title: `${item.signal} - ${item.client.name}`,
      detail: `Cumul 7 jours ${money(item.sevenDayTotal)} sur ${item.client.accounts.length} compte(s).`,
      status: "A revoir",
    });
  });
  renderAlerts();
}

function renderAlerts() {
  const list = document.querySelector("#alertList");
  if (!state.alerts.length) {
    list.innerHTML = `<div class="panel"><strong>Aucune alerte en file.</strong></div>`;
    return;
  }
  list.innerHTML = state.alerts.map((alert) => `
    <article class="alert-card">
      <div>
        <span class="signal ${escapeHTML(alert.severity)}">${escapeHTML(alert.status)}</span>
        <h3>${escapeHTML(alert.title)}</h3>
        <p>${escapeHTML(alert.detail)}</p>
      </div>
      <div class="alert-actions">
        <button class="ghost-btn" data-action="confirmee" data-id="${escapeHTML(alert.id)}">Confirmer</button>
        <button class="ghost-btn" data-action="levee" data-id="${escapeHTML(alert.id)}">Lever</button>
        <button class="ghost-btn" data-action="escaladee" data-id="${escapeHTML(alert.id)}">Escalader</button>
      </div>
    </article>
  `).join("");
}

function renderAudit() {
  document.querySelector("#auditLog").innerHTML = state.audit.map((line) => `<li>${escapeHTML(line)}</li>`).join("");
}

function buildReport() {
  const mainAlert = state.alerts[0];
  const now = new Date().toLocaleString("fr-FR");
  return [
    "RAPPORT CONFIDENTIEL - DEMO SENTINELLECOOP",
    `Horodatage: ${now}`,
    "Referentiel: ONU demo, age 4 minutes, execution locale",
    mainAlert ? `Alerte: ${mainAlert.title}` : "Alerte: aucune alerte active",
    mainAlert ? `Motif: ${mainAlert.detail}` : "Motif: sans objet",
    "Decision: a completer par responsable conformite",
    "Note: donnees clients simulees pour demonstration hackathon.",
  ].join("\n");
}

function exportReport({ download = true } = {}) {
  const report = buildReport();
  document.querySelector("#reportBox").textContent = report;
  if (!download) return;
  const url = URL.createObjectURL(new Blob([report], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "rapport-sentinellecoop.txt";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function switchView(id) {
  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.view === id;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("is-visible", view.id === id));
  if (id === "audit") renderAudit();
}

function initDemo() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => switchView(tab.dataset.view));
  });

  document.querySelector("#screenForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const name = document.querySelector("#clientName").value;
    const result = screenClient(name);
    renderScreenResult(result);
    if (result.decision !== "clear") {
      addAlert({
        id: `SCR-${result.entry.id}`,
        severity: result.decision === "blocking" ? "stop" : "warn",
        title: `Filtrage client - ${name}`,
        detail: `Correspondance ${result.score}% avec ${result.entry.name} (${result.entry.source}).`,
        status: result.decision === "blocking" ? "Bloquante" : "Informative",
      });
      state.audit.unshift(`${new Date().toLocaleTimeString("fr-FR")} - Filtrage ${name}: ${result.score}%`);
      renderAlerts();
      renderAudit();
    }
  });

  document.querySelector("#runDemo").addEventListener("click", () => {
    document.querySelector("#clientName").value = "Djallo Mamadou";
    document.querySelector("#screenForm").dispatchEvent(new Event("submit", { cancelable: true }));
  });

  document.querySelector("#analyzeTransactions").addEventListener("click", renderTransactions);
  document.querySelector("#exportReport").addEventListener("click", exportReport);

  document.querySelector("#alertList").addEventListener("click", (event) => {
    const button = event.target.closest("button[data-id]");
    if (!button) return;
    const alert = state.alerts.find((item) => item.id === button.dataset.id);
    if (!alert) return;
    alert.status = button.dataset.action;
    state.audit.unshift(`${new Date().toLocaleTimeString("fr-FR")} - Alerte ${alert.id} ${button.dataset.action}`);
    renderAlerts();
    renderAudit();
  });

  renderScreenResult(screenClient("Djallo Mamadou"));
  renderTransactions();
  renderAlerts();
  renderAudit();
  exportReport({ download: false });
}

if (typeof document !== "undefined") {
  initDemo();
}

if (typeof module !== "undefined") {
  module.exports = { screenClient, analyzeClient, clients, state, addAlert, escapeHTML };
}
