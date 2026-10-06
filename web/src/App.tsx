import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Clock3,
  Code2,
  Database,
  FileSearch,
  GitCommit,
  Layers3,
  Loader2,
  Lock,
  Network,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Terminal,
  Timer,
  TriangleAlert,
  XCircle,
  Zap
} from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

type EventItem = {
  id: string;
  ts: string;
  service: string;
  kind: string;
  title: string;
};

type Investigation = {
  id: string;
  status: string;
  report: {
    root_cause: string;
    root_cause_service: string;
    evidence_ids: string[];
    confidence: number;
    remediation: string;
  };
  verdict: {
    approved: boolean;
    reasons: string[];
  };
  trace: {
    tool: string;
    args: Record<string, unknown>;
    n_results: number;
  }[];
  timeline: EventItem[];
  tokens: number;
  latency_s: number;
};

function App() {
  const [token, setToken] = useState("");
  const [service, setService] = useState("web");
  const [timestamp, setTimestamp] = useState("2025-01-01T00:08:00Z");
  const [busy, setBusy] = useState(false);
  const [out, setOut] = useState<Investigation | null>(null);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"overview" | "trace" | "evidence">("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<EventItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [approved, setApproved] = useState(false);

  useEffect(() => {
    fetch(`${API}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user: "demo",
        groups: ["public", "sre"]
      })
    })
      .then((r) => {
        if (!r.ok) throw new Error("Unable to authenticate");
        return r.json();
      })
      .then((d) => setToken(d.token))
      .catch((e) => setError(e.message));
  }, []);

  async function investigate() {
    if (!token || !timestamp) return;

    setBusy(true);
    setError("");
    setOut(null);
    setApproved(false);

    try {
      const response = await fetch(`${API}/investigate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          alert_service: service,
          alert_ts: new Date(timestamp).toISOString()
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Investigation failed");
      }

      setOut(data);
      setActiveTab("overview");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Investigation failed");
    } finally {
      setBusy(false);
    }
  }

  async function searchEvents() {
    if (!token || !searchQuery.trim()) return;

    setSearching(true);
    setError("");

    try {
      const response = await fetch(`${API}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          query: searchQuery,
          at: new Date(timestamp).toISOString(),
          minutes: 180
        })
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || "Search failed");

      setSearchResults(data);
      setActiveTab("evidence");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function approve() {
    if (!out) return;

    try {
      const response = await fetch(`${API}/investigations/${out.id}/approve`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Approval failed");
      }

      setApproved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    }
  }

  const evidenceSet = useMemo(
    () => new Set(out?.report.evidence_ids ?? []),
    [out]
  );

  const confidence = Math.round((out?.report.confidence ?? 0) * 100);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="brand-name">OpsMind</div>
            <div className="brand-sub">Incident Intelligence</div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">WORKSPACE</div>

          <button className="nav-item active">
            <Activity size={17} />
            <span>Investigation</span>
          </button>

          <button className="nav-item" onClick={() => setActiveTab("evidence")}>
            <Search size={17} />
            <span>Evidence Search</span>
          </button>

          <button className="nav-item" onClick={() => setActiveTab("trace")}>
            <Terminal size={17} />
            <span>Agent Trace</span>
          </button>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">SYSTEM</div>

          <div className="system-item">
            <span className="status-dot green" />
            <span>API Online</span>
          </div>

          <div className="system-item">
            <span className="status-dot green" />
            <span>Retriever Ready</span>
          </div>

          <div className="system-item">
            <span className="status-dot green" />
            <span>Verifier Ready</span>
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="secure-card">
            <ShieldCheck size={17} />
            <div>
              <strong>Secure Session</strong>
              <span>JWT authenticated</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="eyebrow">
              <span className="pulse" />
              OPERATIONS CENTER
            </div>
            <h1>Incident Investigation</h1>
            <p>AI-assisted root cause analysis with verified operational evidence.</p>
          </div>

          <div className="top-actions">
            <div className="connection">
              <span className="status-dot green" />
              <span>Live</span>
              <ChevronDown size={14} />
            </div>
            <div className="avatar">D</div>
          </div>
        </header>

        <section className="command-panel">
          <div className="command-title">
            <div className="command-icon">
              <Zap size={19} />
            </div>
            <div>
              <h2>Run Investigation</h2>
              <p>Provide the alert context and let the agent investigate.</p>
            </div>
          </div>

          <div className="form-grid">
            <label>
              <span>Alerting Service</span>
              <div className="input-wrap">
                <Layers3 size={16} />
                <input
                  value={service}
                  onChange={(e) => setService(e.target.value)}
                  placeholder="web"
                />
              </div>
            </label>

            <label>
              <span>Alert Timestamp</span>
              <div className="input-wrap">
                <Clock3 size={16} />
                <input
                  value={timestamp}
                  onChange={(e) => setTimestamp(e.target.value)}
                  placeholder="2025-01-01T00:08:00Z"
                />
              </div>
            </label>

            <button
              className="investigate-btn"
              onClick={investigate}
              disabled={!token || busy || !timestamp}
            >
              {busy ? (
                <>
                  <Loader2 className="spin" size={17} />
                  Investigating
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" />
                  Investigate
                </>
              )}
            </button>
          </div>

          {busy && (
            <div className="progress-line">
              <div className="progress-bar" />
              <span>Agent is searching events, changes and dependencies...</span>
            </div>
          )}
        </section>

        {error && (
          <div className="error-banner">
            <TriangleAlert size={17} />
            <span>{error}</span>
            <button onClick={() => setError("")}>×</button>
          </div>
        )}

        {!out && !busy && (
          <EmptyState
            onDemo={() => {
              setService("web");
              setTimestamp("2025-01-01T00:08:00Z");
            }}
          />
        )}

        {out && (
          <>
            <section className="metric-grid">
              <Metric
                icon={<CheckCircle2 />}
                label="Investigation"
                value={out.status === "verified" ? "Verified" : "Insufficient"}
                detail={out.verdict.approved ? "Evidence accepted" : "Review required"}
                good={out.status === "verified"}
              />
              <Metric
                icon={<ShieldCheck />}
                label="Confidence"
                value={`${confidence}%`}
                detail="Agent confidence"
                good={confidence >= 30}
              />
              <Metric
                icon={<Timer />}
                label="Latency"
                value={`${out.latency_s}s`}
                detail="End-to-end"
              />
              <Metric
                icon={<Zap />}
                label="Tokens"
                value={out.tokens.toLocaleString()}
                detail="LLM usage"
              />
            </section>

            <section className="root-card">
              <div className="section-heading">
                <div>
                  <div className="eyebrow">ROOT CAUSE ANALYSIS</div>
                  <h2>Investigation Result</h2>
                </div>

                <div className={`verification-badge ${out.verdict.approved ? "verified" : "failed"}`}>
                  {out.verdict.approved ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
                  {out.verdict.approved ? "VERIFIED" : "REVIEW REQUIRED"}
                </div>
              </div>

              <div className="root-content">
                <div className="root-main">
                  <div className="cause-label">
                    <span className="severity-dot" />
                    ROOT CAUSE
                  </div>
                  <h3>{out.report.root_cause}</h3>

                  <div className="service-pill">
                    <Database size={14} />
                    {out.report.root_cause_service}
                  </div>
                </div>

                <div className="confidence-ring">
                  <div
                    className="ring"
                    style={{ "--progress": `${confidence * 3.6}deg` } as React.CSSProperties}
                  >
                    <div>
                      <strong>{confidence}%</strong>
                      <span>confidence</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="remediation">
                <div className="remediation-icon">
                  <ArrowRight size={16} />
                </div>
                <div>
                  <span>RECOMMENDED REMEDIATION</span>
                  <p>{out.report.remediation}</p>
                </div>
              </div>
            </section>

            <div className="tabs">
              <button
                className={activeTab === "overview" ? "selected" : ""}
                onClick={() => setActiveTab("overview")}
              >
                <Network size={16} />
                Timeline
              </button>
              <button
                className={activeTab === "trace" ? "selected" : ""}
                onClick={() => setActiveTab("trace")}
              >
                <Terminal size={16} />
                Agent Trace
                <span>{out.trace.length}</span>
              </button>
              <button
                className={activeTab === "evidence" ? "selected" : ""}
                onClick={() => setActiveTab("evidence")}
              >
                <FileSearch size={16} />
                Evidence
                <span>{out.report.evidence_ids.length}</span>
              </button>
            </div>

            {activeTab === "overview" && (
              <Timeline
                events={out.timeline}
                evidence={evidenceSet}
              />
            )}

            {activeTab === "trace" && <Trace trace={out.trace} />}

            {activeTab === "evidence" && (
              <EvidencePanel
                investigation={out}
                query={searchQuery}
                setQuery={setSearchQuery}
                results={searchResults}
                searching={searching}
                onSearch={searchEvents}
              />
            )}

            <section className="verification-card">
              <div className="verification-header">
                <div className="verification-title">
                  <div className="shield-box">
                    <ShieldCheck size={19} />
                  </div>
                  <div>
                    <h3>Verifier</h3>
                    <p>Independent evidence validation</p>
                  </div>
                </div>

                <span className={out.verdict.approved ? "pass-label" : "fail-label"}>
                  {out.verdict.approved ? "PASSED" : "FAILED"}
                </span>
              </div>

              <div className="checks">
                <CheckRow
                  ok={out.report.evidence_ids.length > 0}
                  text={
                    out.report.evidence_ids.length > 0
                      ? `${out.report.evidence_ids.length} valid evidence citation(s)`
                      : "No valid evidence citations"
                  }
                />
                <CheckRow
                  ok={out.verdict.reasons.every((r) => !r.includes("hallucinated"))}
                  text="No hallucinated evidence IDs"
                />
                <CheckRow
                  ok={out.verdict.approved}
                  text="Root-cause claim supported by evidence"
                />
              </div>

              {out.verdict.reasons.length > 0 && (
                <div className="verifier-reasons">
                  {out.verdict.reasons.map((reason, i) => (
                    <div key={i}>
                      <AlertTriangle size={14} />
                      {reason}
                    </div>
                  ))}
                </div>
              )}

              {out.status === "verified" && (
                <div className="approval-area">
                  {approved ? (
                    <div className="approved-message">
                      <CheckCircle2 size={18} />
                      Approval recorded successfully. No production action was executed.
                    </div>
                  ) : (
                    <button className="approve-btn" onClick={approve}>
                      <Check size={16} />
                      Approve Fix Suggestion
                    </button>
                  )}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
  good
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  detail: string;
  good?: boolean;
}) {
  return (
    <div className="metric-card">
      <div className={`metric-icon ${good ? "good" : ""}`}>{icon}</div>
      <div className="metric-info">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function EmptyState({ onDemo }: { onDemo: () => void }) {
  return (
    <section className="empty-state">
      <div className="empty-orbit">
        <div className="orbit-ring ring-one" />
        <div className="orbit-ring ring-two" />
        <div className="empty-core">
          <Sparkles size={27} />
        </div>
      </div>

      <h2>Ready to investigate an incident</h2>
      <p>
        OpsMind will correlate logs, deployments, configuration changes and
        service dependencies to identify a probable root cause.
      </p>

      <div className="capability-row">
        <span><Search size={14} /> Hybrid Retrieval</span>
        <span><Network size={14} /> Dependency Graph</span>
        <span><ShieldCheck size={14} /> Evidence Verification</span>
      </div>

      <button className="demo-btn" onClick={onDemo}>
        <RefreshCw size={15} />
        Load Demo Incident
      </button>
    </section>
  );
}

function Timeline({
  events,
  evidence
}: {
  events: EventItem[];
  evidence: Set<string>;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="eyebrow">EVENT CORRELATION</div>
          <h2>Incident Timeline</h2>
        </div>
        <span className="event-count">{events.length} events</span>
      </div>

      <div className="timeline">
        {events.map((event, index) => {
          const cited = evidence.has(event.id);

          return (
            <div className={`timeline-item ${cited ? "cited" : ""}`} key={event.id}>
              <div className="timeline-time">
                {new Date(event.ts).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit"
                })}
              </div>

              <div className="timeline-line">
                <div className={`timeline-node ${cited ? "highlight" : ""}`}>
                  {cited ? <Check size={12} /> : <GitCommit size={12} />}
                </div>
              </div>

              <div className="timeline-content">
                <div className="event-top">
                  <span className="event-service">{event.service}</span>
                  <span className={`kind ${event.kind}`}>{event.kind.replace("_", " ")}</span>
                  {cited && <span className="cited-tag">CITED EVIDENCE</span>}
                </div>
                <h3>{event.title}</h3>
                <code>{event.id}</code>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Trace({
  trace
}: {
  trace: Investigation["trace"];
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="eyebrow">AGENT REASONING PIPELINE</div>
          <h2>Tool Execution Trace</h2>
        </div>
        <span className="event-count">{trace.length} calls</span>
      </div>

      <div className="trace-list">
        {trace.map((item, index) => (
          <div className="trace-item" key={`${item.tool}-${index}`}>
            <div className="trace-number">{String(index + 1).padStart(2, "0")}</div>

            <div className="trace-icon">
              {item.tool.includes("search") ? (
                <Search size={16} />
              ) : item.tool.includes("change") ? (
                <GitCommit size={16} />
              ) : (
                <Network size={16} />
              )}
            </div>

            <div className="trace-body">
              <div className="trace-title">
                <strong>{item.tool}</strong>
                <span>{item.n_results} result{item.n_results === 1 ? "" : "s"}</span>
              </div>

              <pre>{JSON.stringify(item.args, null, 2)}</pre>
            </div>

            <CheckCircle2 className="trace-ok" size={17} />
          </div>
        ))}
      </div>
    </section>
  );
}

function EvidencePanel({
  investigation,
  query,
  setQuery,
  results,
  searching,
  onSearch
}: {
  investigation: Investigation;
  query: string;
  setQuery: (v: string) => void;
  results: EventItem[];
  searching: boolean;
  onSearch: () => void;
}) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="eyebrow">RETRIEVAL</div>
          <h2>Evidence Explorer</h2>
        </div>
      </div>

      <div className="search-bar">
        <Search size={17} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearch()}
          placeholder="Search operational events..."
        />
        <button onClick={onSearch} disabled={searching || !query.trim()}>
          {searching ? <Loader2 className="spin" size={15} /> : "Search"}
        </button>
      </div>

      <div className="evidence-list">
        {results.length === 0 ? (
          <div className="evidence-empty">
            <FileSearch size={25} />
            <p>Search the event store to inspect operational evidence.</p>
          </div>
        ) : (
          results.map((event) => {
            const cited = investigation.report.evidence_ids.includes(event.id);

            return (
              <div className={`evidence-row ${cited ? "cited" : ""}`} key={event.id}>
                <div className="evidence-icon">
                  {cited ? <Check size={15} /> : <FileSearch size={15} />}
                </div>
                <div className="evidence-content">
                  <div>
                    <span>{event.service}</span>
                    <span>·</span>
                    <span>{event.kind}</span>
                    {cited && <b> CITED</b>}
                  </div>
                  <strong>{event.title}</strong>
                  <small>{event.id}</small>
                </div>
                <time>
                  {new Date(event.ts).toLocaleTimeString()}
                </time>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

function CheckRow({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div className="check-row">
      {ok ? (
        <CheckCircle2 className="check-pass" size={17} />
      ) : (
        <XCircle className="check-fail" size={17} />
      )}
      <span>{text}</span>
    </div>
  );
}

export default App;
