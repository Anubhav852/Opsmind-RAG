import { useEffect, useState } from "react";

const API = "http://localhost:8000";
type Ev = { id: string; ts: string; service: string; kind: string; title: string };

export default function App() {
  const [token, setToken] = useState("");
  const [service, setService] = useState("checkout");
  const [ts, setTs] = useState("");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<any>(null);

  useEffect(() => {
    fetch(`${API}/auth/token`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: "demo", groups: ["public", "sre"] }),
    }).then(r => r.json()).then(d => setToken(d.token));
  }, []);

  async function run() {
    setBusy(true); setOut(null);
    const r = await fetch(`${API}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ alert_service: service, alert_ts: new Date(ts).toISOString() }),
    });
    setOut(await r.json()); setBusy(false);
  }
  async function approve() {
    await fetch(`${API}/investigations/${out.id}/approve`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
    alert("Approval recorded (no automatic production action).");
  }

  const cited = new Set<string>(out?.report?.evidence_ids ?? []);
  return (
    <div style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "system-ui" }}>
      <h1>OpsMind</h1>
      <input value={service} onChange={e => setService(e.target.value)} placeholder="alert service" />
      <input value={ts} onChange={e => setTs(e.target.value)} placeholder="alert ts (ISO, from ground_truth.jsonl)" style={{ width: 360 }} />
      <button onClick={run} disabled={!token || busy || !ts}>{busy ? "Investigating..." : "Investigate"}</button>
      {out && (
        <>
          <h2>Status: {out.status} (confidence {out.report.confidence})</h2>
          <p><b>Root cause:</b> {out.report.root_cause}</p>
          <p><b>Suggested fix:</b> {out.report.remediation}</p>
          {out.verdict.reasons.length > 0 && <p style={{ color: "crimson" }}>Verifier: {out.verdict.reasons.join("; ")}</p>}
          <h3>Timeline (cited evidence highlighted)</h3>
          <ul>
            {out.timeline.map((e: Ev) => (
              <li key={e.id} style={{ background: cited.has(e.id) ? "#fff3b0" : "transparent" }}>
                {new Date(e.ts).toLocaleTimeString()} [{e.service}/{e.kind}] {e.title}
              </li>
            ))}
          </ul>
          {out.status === "verified" && <button onClick={approve}>Approve fix suggestion</button>}
          <small>{out.tokens} tokens, {out.latency_s}s</small>
        </>
      )}
    </div>
  );
}
