// Sentinelle réseau : ping actif périodique, pas seulement navigator.onLine
// (qui reste "true" même quand la 2G/3G ne passe plus rien). Hystérésis pour
// ne pas clignoter ONLINE/OFFLINE sur un réseau instable.
const CHECK_INTERVAL_ONLINE_MS = 12_000;
const CHECK_INTERVAL_OFFLINE_MS = 20_000;
const FAILURES_TO_GO_OFFLINE = 2;
const PING_TIMEOUT_MS = 4_000;

export function createConnectivitySentinel(apiBaseUrl, onChange) {
  let state = "online"; // hypothèse de départ : le système "est" internet
  let consecutiveFailures = 0;
  let timer = null;
  let stopped = false;

  async function check() {
    if (stopped) return;
    try {
      const controller = new AbortController();
      const t = setTimeout(() => controller.abort(), PING_TIMEOUT_MS);
      const res = await fetch(`${apiBaseUrl}/health`, { signal: controller.signal });
      clearTimeout(t);
      if (!res.ok) throw new Error(`status ${res.status}`);

      consecutiveFailures = 0;
      if (state !== "online") {
        state = "online";
        onChange(state); // bascule silencieuse : réveille juste le worker de synchro
      }
    } catch {
      consecutiveFailures += 1;
      if (consecutiveFailures >= FAILURES_TO_GO_OFFLINE && state !== "offline") {
        state = "offline";
        onChange(state); // bascule silencieuse : le worker arrête simplement d'émettre
      }
    } finally {
      if (!stopped) {
        const delay = state === "online" ? CHECK_INTERVAL_ONLINE_MS : CHECK_INTERVAL_OFFLINE_MS;
        timer = setTimeout(check, delay);
      }
    }
  }

  return {
    start: () => check(),
    stop: () => {
      stopped = true;
      clearTimeout(timer);
    },
    getState: () => state,
  };
}
