export async function pushBatch(apiBaseUrl, agencyId, items) {
  const res = await fetch(`${apiBaseUrl}/sync/push`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agency_id: agencyId, items }),
  });
  if (!res.ok) throw new Error(`push failed: ${res.status}`);
  return res.json();
}

export async function pullDelta(apiBaseUrl, since) {
  const res = await fetch(`${apiBaseUrl}/sync/pull?since=${encodeURIComponent(since)}`);
  if (!res.ok) throw new Error(`pull failed: ${res.status}`);
  return res.json();
}
