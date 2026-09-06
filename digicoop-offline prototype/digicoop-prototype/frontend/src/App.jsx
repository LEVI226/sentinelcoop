import { useState } from "react";
import { getDb, unlockDatabase } from "./db/localDb";
import { startSyncWorker } from "./offline/syncWorker";
import { screenClient } from "./engine/screening";
import ClientForm from "./components/ClientForm";
import ScreeningResult from "./components/ScreeningResult";
import AlertsList from "./components/AlertsList";
import StatusDot from "./components/StatusDot";
import PinGate from "./components/PinGate";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const AGENCY_ID = import.meta.env.VITE_AGENCY_ID || "ouagadougou-01";

export default function App() {
  const [ready, setReady] = useState(false);
  const [tabConflict, setTabConflict] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // Seul point du code où les axes offline et moteur IA se rencontrent :
  // on injecte screenClient dans le worker, il ne l'importe jamais lui-même.
  // Le code du terminal n'est demandé qu'ici, une fois, via PinGate — voir
  // db/crypto.js pour le modèle de menace exact du chiffrement au repos.
  async function handleUnlock(pin) {
    const { plainBytes } = await unlockDatabase(pin); // lève une erreur si code incorrect
    await getDb(plainBytes);

    // Seam de test : un test Playwright peut poser cette variable avant de
    // charger la page pour réduire batchSize/backoff/dead-letter à quelques
    // centaines de ms, sans jamais toucher au comportement de production.
    const testOverrides = typeof window !== "undefined" ? window.__DIGICOOP_TEST_SYNC_CONFIG__ : undefined;

    startSyncWorker({
      baseUrl: API_BASE_URL,
      agency: AGENCY_ID,
      onRescreenClient: screenClient,
      onMultiTabConflict: () => setTabConflict(true),
      ...testOverrides,
    });
    setReady(true);
  }

  function handleResult(data) {
    setLastResult(data);
    setRefreshKey((k) => k + 1);
    // Plus besoin d'appeler persist() ici : chaque run() planifie déjà une
    // persistance différée (voir db/localDb.js schedulePersist()).
  }

  if (!ready) return <PinGate onUnlock={handleUnlock} />;

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24, maxWidth: 640, margin: "0 auto" }}>
      <h1 style={{ fontSize: 20, marginBottom: 4 }}>Terminal agent — Filtrage LBC/FT/FP</h1>
      <p style={{ fontSize: 12, color: "#57655F", marginTop: 0 }}>Agence : {AGENCY_ID}</p>
      {tabConflict && (
        <p
          role="alert"
          style={{ fontSize: 12, color: "#8A4B00", background: "#FFF3DF", border: "1px solid #E8B96A", borderRadius: 6, padding: "8px 12px" }}
        >
          Ce terminal semble déjà ouvert dans un autre onglet sur cet appareil. La base locale
          n'est pas partagée entre onglets : travailler dans les deux à la fois peut faire perdre
          des opérations. Fermez cet onglet ou l'autre avant de continuer.
        </p>
      )}
      <StatusDot />
      <ClientForm onResult={handleResult} />
      <ScreeningResult data={lastResult} />
      <h2 style={{ fontSize: 16, marginTop: 32 }}>Alertes locales</h2>
      <AlertsList refreshKey={refreshKey} />
    </main>
  );
}
