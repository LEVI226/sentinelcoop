/**
 * CIF GUARD PRO — INTERACTIVE SUITE
 * Micro-interactions, Offline Sync, Table Skeletons, Filter/Sort & Audit Modals
 */

(function () {
  'use strict';

  // --- 1. Notification Toast Manager ---
  window.showToast = function (message, type = 'success') {
    const existing = document.getElementById('cif-global-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'cif-global-toast';
    toast.className = `fixed bottom-6 right-6 z-[9999] flex items-center gap-3 rounded-xl px-5 py-4 text-sm font-semibold text-white shadow-2xl toast-slide-up ${
      type === 'error'
        ? 'bg-red-600 ring-2 ring-red-300'
        : type === 'warning'
        ? 'bg-amber-600 ring-2 ring-amber-300'
        : 'bg-emerald-600 ring-2 ring-emerald-300'
    }`;

    const icon =
      type === 'error'
        ? 'lucide:alert-circle'
        : type === 'warning'
        ? 'lucide:alert-triangle'
        : 'lucide:check-circle-2';

    toast.innerHTML = `
      <iconify-icon icon="${icon}" class="text-xl shrink-0"></iconify-icon>
      <div>
        <p class="text-sm font-bold">${message}</p>
      </div>
      <button onclick="this.parentElement.remove()" class="ml-2 text-white/80 hover:text-white text-xs">&times;</button>
    `;

    document.body.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 4000);
  };

  // --- 2. Mode Hors-Ligne & Synchronisation Résiliente ---
  let isOfflineMode = true; // Démarre par défaut en mode hors-ligne pour la démonstration

  window.toggleOfflineStatus = function () {
    const modal = document.getElementById('cif-offline-modal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }
  };

  window.closeOfflineModal = function () {
    const modal = document.getElementById('cif-offline-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  };

  window.triggerOfflineSync = function () {
    const syncBtn = document.getElementById('offline-sync-btn');
    if (syncBtn) {
      syncBtn.disabled = true;
      syncBtn.innerHTML = `
        <iconify-icon icon="lucide:loader-2" class="text-base animate-spin"></iconify-icon>
        Synchronisation en cours...
      `;
    }

    setTimeout(() => {
      isOfflineMode = !isOfflineMode;
      window.updateNetworkBadgeUI(isOfflineMode);
      window.closeOfflineModal();

      if (syncBtn) {
        syncBtn.disabled = false;
        syncBtn.innerHTML = `
          <iconify-icon icon="lucide:refresh-cw" class="text-base"></iconify-icon>
          Forcer la synchronisation maintenant
        `;
      }

      if (!isOfflineMode) {
        window.showToast('Succès : 3 actions locales synchronisées avec le serveur central CIF Guard.');
      } else {
        window.showToast('Mode hors-ligne réactivé — 3 actions en cache local.', 'warning');
      }
    }, 1200);
  };

  window.updateNetworkBadgeUI = function (offline) {
    const badgeContainer = document.getElementById('network-status-widget');
    if (!badgeContainer) return;

    if (offline) {
      badgeContainer.className =
        'flex items-center gap-2 cursor-pointer rounded-full bg-amber-50 border border-amber-300 px-3 py-1 text-xs font-semibold text-amber-800 hover:bg-amber-100 transition shadow-xs badge-offline-pulse';
      badgeContainer.title = 'Cliquer pour examiner la file de synchronisation locale';
      badgeContainer.innerHTML = `
        <iconify-icon icon="lucide:wifi-off" class="text-amber-600 text-sm"></iconify-icon>
        <span>Mode hors-ligne &bull; 3 actions en attente</span>
      `;
    } else {
      badgeContainer.className =
        'flex items-center gap-2 cursor-pointer rounded-full bg-emerald-50 border border-emerald-200 px-3 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 transition shadow-xs';
      badgeContainer.title = 'Connexion active — Cliquez pour simuler le mode hors-ligne';
      badgeContainer.innerHTML = `
        <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
        <iconify-icon icon="lucide:wifi" class="text-emerald-600 text-sm"></iconify-icon>
        <span>Synchronisé (En ligne)</span>
      `;
    }
  };

  // --- 3. Modale d'Action Irréversible avec Audit Trail ---
  window.currentConfirmCallback = null;

  window.openAuditConfirmModal = function (title, message, onConfirm) {
    let modal = document.getElementById('cif-audit-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'cif-audit-modal';
      modal.className =
        'fixed inset-0 z-50 hidden items-center justify-center audit-modal-backdrop px-4';
      modal.innerHTML = `
        <div class="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in duration-150">
          <div class="flex items-start gap-4">
            <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-600 ring-4 ring-red-50">
              <iconify-icon icon="lucide:shield-alert" class="text-2xl"></iconify-icon>
            </span>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="rounded bg-red-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-red-700">Action Irréversible</span>
                <span class="text-xs text-slate-400">Piste d'audit CENTIF / BCEAO</span>
              </div>
              <h2 id="cif-audit-modal-title" class="mt-1 text-lg font-bold text-night">Confirmer cette action</h2>
              <p id="cif-audit-modal-desc" class="mt-2 text-sm leading-6 text-slate-600">
                Êtes-vous sûr de vouloir clôturer cette alerte ? Cette action sera enregistrée de manière inaltérable dans le journal d'audit.
              </p>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3 border-t border-slate-100 pt-4">
            <button onclick="window.closeAuditConfirmModal()" class="h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition">
              Annuler
            </button>
            <button id="cif-audit-confirm-execute-btn" class="h-10 rounded-lg bg-red-600 px-5 text-sm font-semibold text-white hover:bg-red-700 transition shadow-sm flex items-center gap-2">
              <iconify-icon icon="lucide:check" class="text-base"></iconify-icon>
              Confirmer et signer dans l'audit
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      document
        .getElementById('cif-audit-confirm-execute-btn')
        .addEventListener('click', () => {
          if (window.currentConfirmCallback) {
            window.currentConfirmCallback();
          }
          window.closeAuditConfirmModal();
        });
    }

    if (title) document.getElementById('cif-audit-modal-title').textContent = title;
    if (message) document.getElementById('cif-audit-modal-desc').textContent = message;
    window.currentConfirmCallback = onConfirm;

    modal.classList.remove('hidden');
    modal.classList.add('flex');
  };

  window.closeAuditConfirmModal = function () {
    const modal = document.getElementById('cif-audit-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  };

  // --- 4. Simulation Skeleton Loading pour tableaux ---
  window.simulateSkeletonLoading = function (tableContainerId) {
    const container = document.getElementById(tableContainerId);
    if (!container) return;

    const table = container.querySelector('table');
    if (!table) return;

    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    // Sauvegarde du HTML d'origine
    if (!tbody.dataset.originalHtml) {
      tbody.dataset.originalHtml = tbody.innerHTML;
    }

    const colCount = table.querySelectorAll('thead th').length || 7;

    // Création de 4 lignes de skeleton
    let skeletonHtml = '';
    for (let i = 0; i < 4; i++) {
      skeletonHtml += `<tr class="skeleton-row border-b border-slate-100">`;
      for (let j = 0; j < colCount; j++) {
        const width = j === 1 ? 'w-36' : j === 2 ? 'w-48' : 'w-20';
        skeletonHtml += `<td><span class="skeleton-box h-4 ${width}"></span></td>`;
      }
      skeletonHtml += `</tr>`;
    }

    tbody.innerHTML = skeletonHtml;

    // Restauration après 1.2s avec notification
    setTimeout(() => {
      tbody.innerHTML = tbody.dataset.originalHtml;
      window.showToast('Données du tableau actualisées en direct.');
    }, 1100);
  };

  // --- 5. Recherche & Tri dynamique pour tableaux ---
  window.filterTableRows = function (input, tableContainerId) {
    const query = input.value.toLowerCase().trim();
    const container = document.getElementById(tableContainerId);
    if (!container) return;

    const rows = container.querySelectorAll('tbody tr');
    let visibleCount = 0;

    rows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      if (text.includes(query)) {
        row.style.display = '';
        visibleCount++;
      } else {
        row.style.display = 'none';
      }
    });

    const countEl = document.getElementById(tableContainerId + '-count');
    if (countEl) {
      countEl.textContent = `${visibleCount} alerte${visibleCount > 1 ? 's' : ''}`;
    }
  };

  window.filterByRisk = function (riskLevel, tableContainerId, btn) {
    const container = document.getElementById(tableContainerId);
    if (!container) return;

    // Reset styles on filter buttons
    const filterGroup = btn.parentElement;
    if (filterGroup) {
      filterGroup.querySelectorAll('button').forEach((b) => {
        b.classList.remove('bg-institution', 'text-white', 'border-institution');
        b.classList.add('bg-white', 'text-slate-600', 'border-slate-200');
      });
      btn.classList.remove('bg-white', 'text-slate-600', 'border-slate-200');
      btn.classList.add('bg-institution', 'text-white', 'border-institution');
    }

    const rows = container.querySelectorAll('tbody tr');
    let visibleCount = 0;

    rows.forEach((row) => {
      if (riskLevel === 'ALL') {
        row.style.display = '';
        visibleCount++;
      } else if (riskLevel === 'CRITICAL') {
        const isCrit =
          row.classList.contains('critical-row') ||
          row.innerText.toLowerCase().includes('critique');
        row.style.display = isCrit ? '' : 'none';
        if (isCrit) visibleCount++;
      } else if (riskLevel === 'OVERDUE') {
        const isOver =
          row.innerText.includes('J+') ||
          row.innerText.toLowerCase().includes('retard') ||
          row.innerText.includes('4 j') ||
          row.innerText.includes('5 j');
        row.style.display = isOver ? '' : 'none';
        if (isOver) visibleCount++;
      } else if (riskLevel === 'MEDIUM') {
        const isMed =
          row.innerText.toLowerCase().includes('moyen') ||
          row.innerText.toLowerCase().includes('faible');
        row.style.display = isMed ? '' : 'none';
        if (isMed) visibleCount++;
      }
    });

    const countEl = document.getElementById(tableContainerId + '-count');
    if (countEl) {
      countEl.textContent = `${visibleCount} résultat${visibleCount > 1 ? 's' : ''}`;
    }
  };

  // --- 6. Quick Actions ---
  window.quickAssignAlert = function (alertId, btn) {
    btn.innerHTML = `<iconify-icon icon="lucide:check" class="text-emerald-600"></iconify-icon> Assigné`;
    btn.classList.add('bg-emerald-50', 'text-emerald-700', 'border-emerald-200');
    window.showToast(`Alerte ${alertId} assignée à Mariam Kaboré.`);
  };

  window.quickCloseAlert = function (alertId) {
    window.openAuditConfirmModal(
      `Clôturer l'alerte ${alertId}`,
      `Êtes-vous sûr de vouloir clôturer cette alerte ? Cette action sera enregistrée dans le journal d'audit conformément aux normes CENTIF / BCEAO.`,
      () => {
        window.showToast(`Alerte ${alertId} clôturée avec succès. Piste d'audit générée.`);
      }
    );
  };

  // --- 7. Validation obligatoire de la justification pour "Classer sans suite" ---
  window.handleDismissAlert = function () {
    const reasonInput = document.getElementById('dismiss-reason');
    const confirmCheckbox = document.getElementById('dismiss-confirm');

    if (!reasonInput) return;

    const val = reasonInput.value.trim();
    if (val.length < 20) {
      reasonInput.focus();
      reasonInput.classList.add('ring-2', 'ring-red-500', 'border-red-500');

      let err = document.getElementById('dismiss-error-msg');
      if (!err) {
        err = document.createElement('p');
        err.id = 'dismiss-error-msg';
        err.className = 'mt-1.5 text-xs font-semibold text-red-600 flex items-center gap-1';
        err.innerHTML = '<iconify-icon icon="lucide:alert-circle"></iconify-icon> Justification obligatoire (minimum 20 caractères pour conformité audit CENTIF)';
        reasonInput.parentElement.appendChild(err);
      }
      window.showToast('Erreur : Justification obligatoire d\'au moins 20 caractères.', 'error');
      return;
    }

    // Retirer erreur si valide
    reasonInput.classList.remove('ring-2', 'ring-red-500', 'border-red-500');
    const err = document.getElementById('dismiss-error-msg');
    if (err) err.remove();

    if (confirmCheckbox && !confirmCheckbox.checked) {
      window.showToast('Veuillez cocher la case confirmant l\'absence de risque.', 'warning');
      return;
    }

    // Ouvrir la modale d'audit officielle
    window.openAuditConfirmModal(
      'Classer cette alerte sans suite',
      `Êtes-vous sûr de vouloir classer l'alerte sans suite avec le motif saisi ? Cette décision et la justification fournie seront archivées de façon inaltérable dans le journal d'audit BCEAO/CENTIF.`,
      () => {
        // Ajouter à l'historique sur la page
        const historyList = document.querySelector('ol.border-slate-200');
        if (historyList) {
          const now = new Date();
          const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
          const newEntry = document.createElement('li');
          newEntry.className = 'relative pb-6 pl-7 animate-in fade-in';
          newEntry.innerHTML = `
            <span class="absolute -left-[9px] top-0 flex h-4 w-4 items-center justify-center rounded-full border-2 border-white bg-slate-600 ring-1 ring-slate-600"></span>
            <p class="text-sm font-semibold text-night">Aujourd'hui · ${timeStr} — Alerte classée sans suite</p>
            <p class="mt-1 text-sm text-slate-500">Mariam Kaboré · Motif : « ${val.substring(0, 70)}... »</p>
          `;
          historyList.insertBefore(newEntry, historyList.firstChild);
        }
        window.showToast('Alerte classée sans suite. Entrée horodatée dans le journal d\'audit.');
      }
    );
  };

  // --- 8. Initialisation au chargement du DOM ---
  document.addEventListener('DOMContentLoaded', function () {
    // Initialiser le widget de statut réseau
    window.updateNetworkBadgeUI(isOfflineMode);

    // Injection de la modale de détails du mode hors-ligne
    if (!document.getElementById('cif-offline-modal')) {
      const offlineModal = document.createElement('div');
      offlineModal.id = 'cif-offline-modal';
      offlineModal.className =
        'fixed inset-0 z-50 hidden items-center justify-center audit-modal-backdrop px-4';
      offlineModal.innerHTML = `
        <div class="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl border border-slate-200">
          <div class="flex items-start gap-3">
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
              <iconify-icon icon="lucide:wifi-off" class="text-xl"></iconify-icon>
            </span>
            <div>
              <h3 class="text-base font-bold text-night">Mode Hors-Ligne CIF Guard</h3>
              <p class="text-xs text-slate-500">Résilience pour zones à connectivité limitée</p>
            </div>
          </div>
          <div class="mt-4 rounded-lg bg-slate-50 p-3.5 border border-slate-200">
            <p class="text-xs font-semibold text-slate-700 mb-2">3 actions locales en attente de synchronisation :</p>
            <ul class="space-y-2 text-xs text-slate-600">
              <li class="flex items-center justify-between">
                <span>&bull; Clôture alerte <strong>ALT-2026-001847</strong></span>
                <span class="text-[10px] text-slate-400">14:45</span>
              </li>
              <li class="flex items-center justify-between">
                <span>&bull; Note KYC client <strong>CIF-2026-00389</strong></span>
                <span class="text-[10px] text-slate-400">14:41</span>
              </li>
              <li class="flex items-center justify-between">
                <span>&bull; Réassignation alerte à <strong>M. Kaboré</strong></span>
                <span class="text-[10px] text-slate-400">14:38</span>
              </li>
            </ul>
          </div>
          <p class="mt-3 text-[11px] text-slate-500 leading-relaxed">
            Les données sont sécurisées localement avec chiffrement AES-256. La synchronisation s'effectue automatiquement dès détection de connectivité.
          </p>
          <div class="mt-5 flex gap-2">
            <button onclick="window.closeOfflineModal()" class="flex-1 h-9 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition">
              Fermer
            </button>
            <button id="offline-sync-btn" onclick="window.triggerOfflineSync()" class="flex-1 h-9 rounded-lg bg-institution text-xs font-semibold text-white hover:bg-blue-800 transition flex items-center justify-center gap-1.5 shadow-xs">
              <iconify-icon icon="lucide:refresh-cw" class="text-sm"></iconify-icon>
              Synchroniser
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(offlineModal);
    }

    // Brancher le bouton "dismiss-btn" s'il existe sur la page de détail
    const dismissBtn = document.getElementById('dismiss-btn');
    if (dismissBtn) {
      dismissBtn.removeAttribute('onclick');
      dismissBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        window.handleDismissAlert();
      });
    }

    // Brancher le bouton "close-alert-btn" s'il existe
    const closeAlertBtn = document.getElementById('close-alert-btn');
    if (closeAlertBtn) {
      closeAlertBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const reason = document.getElementById('close-reason');
        if (reason && reason.value.trim().length < 20) {
          reason.focus();
          reason.classList.add('ring-2', 'ring-red-500');
          window.showToast('Veuillez fournir une justification de clôture (min. 20 caractères).', 'error');
          return;
        }
        window.openAuditConfirmModal(
          'Clôturer définitivement cette alerte',
          'Êtes-vous sûr de vouloir clôturer cette alerte ? Cette action sera enregistrée dans le journal d\'audit conformément aux normes CENTIF / BCEAO.',
          () => {
            window.showToast('Alerte clôturée avec succès. Enregistrée dans le journal d\'audit.');
          }
        );
      });
    }

    // Brancher le bouton "suspect-btn" s'il existe
    const suspectBtn = document.getElementById('suspect-btn');
    if (suspectBtn) {
      suspectBtn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        const reason = document.getElementById('suspect-reason');
        if (reason && reason.value.trim().length < 20) {
          reason.focus();
          reason.classList.add('ring-2', 'ring-red-500');
          window.showToast('Veuillez détailler la justification du cas suspect (min. 20 caractères).', 'error');
          return;
        }
        window.openAuditConfirmModal(
          'Déclarer comme Cas Suspect (CENOS/CENTIF)',
          'Cette action transmettra le dossier au responsable conformité pour déclaration de soupçon formelle auprès des autorités (CENTIF). Êtes-vous certain de confirmer ?',
          () => {
            window.showToast('Cas suspect déclaré et transmis à la CENTIF. Piste d\'audit verrouillée.');
          }
        );
      });
    }
  });
})();
