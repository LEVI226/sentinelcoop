const assert = require("assert");
const { screenClient, analyzeClient, clients, state, addAlert, escapeHTML } = require("./app.js");

const diallo = screenClient("Djallo Mamadou");
assert(diallo.score >= 90, "Djallo Mamadou should trigger a strong match");
assert.strictEqual(diallo.decision, "blocking");

const clear = screenClient("Awa Sawadogo");
assert(clear.score < 75, "Unrelated local client should not trigger an alert");

const risky = analyzeClient(clients[0]);
assert.strictEqual(risky.signal, "Fractionnement");
assert(risky.accountTotal > 1000000, "Multi-account balance should be consolidated");

const before = state.alerts.length;
addAlert({ id: "TEST-1", severity: "warn", title: "Test", detail: "Test", status: "A revoir" });
assert.strictEqual(state.alerts.length, before + 1);

assert.strictEqual(
  escapeHTML('<img src=x onerror="alert(1)">'),
  "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;"
);

console.log("Demo logic tests passed");
