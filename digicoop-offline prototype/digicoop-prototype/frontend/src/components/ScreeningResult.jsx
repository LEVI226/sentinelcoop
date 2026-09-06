const BADGES = {
  autorisee: { label: "Autorisée — voie rapide", color: "#1F6F5C" },
  autorisee_surveillee: { label: "Autorisée, sous surveillance", color: "#B8862E" },
  retenue: { label: "Retenue — correspondance probable", color: "#B8862E" },
};

export default function ScreeningResult({ data }) {
  if (!data) return null;
  const { client, result } = data;
  const badge = BADGES[result.decision];

  return (
    <div style={{ border: "1px solid #D9DFD8", borderRadius: 10, padding: 16, marginTop: 16 }}>
      <div style={{ fontWeight: 700 }}>{client.full_name}</div>
      <div style={{ color: badge.color, fontWeight: 600, marginTop: 4 }}>{badge.label}</div>

      {result.nameMatches.length > 0 && (
        <div style={{ fontSize: 13, marginTop: 8 }}>
          Correspondance : {result.nameMatches[0].entry.full_name} (
          {Math.round(result.nameMatches[0].score * 100)}% de similarité, {result.nameMatches[0].entry.category})
        </div>
      )}

      {result.ruleResult.flags.length > 0 && (
        <ul style={{ fontSize: 13, marginTop: 8, paddingLeft: 18 }}>
          {result.ruleResult.flags.map((f) => (
            <li key={f.rule}>{f.detail}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
