"use client";

import { useEffect, useMemo, useState } from "react";

type Provenance = {
  id: string;
  parent_id?: string | null;
  prompt: string;
  model: string;
  status: string;
  created_at: string;
  asset_url?: string | null;
  asset_sha256?: string | null;
  manifest_sha256?: string | null;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const stages = [
  { name: "Brief analysis", provider: "GMI / Qwen 3", time: "0.8s" },
  { name: "Key visual", provider: "Stability AI", time: "3.4s" },
  { name: "Voice track", provider: "ElevenLabs", time: "2.1s" },
  { name: "Motion render", provider: "Runway", time: "6.8s" },
  { name: "Provenance + B2", provider: "Genblaze", time: "0.5s" },
];

const events = [
  ["00:00.000", "run.created", "Pipeline run_7F2A accepted"],
  ["00:00.184", "brief.parsed", "3 deliverables · en-US · 15 sec"],
  ["00:00.812", "image.started", "Stability adapter · retry policy 2×"],
  ["00:03.476", "asset.stored", "key-visual.webp → b2://traceframe/runs/7F2A"],
  ["00:03.522", "voice.started", "ElevenLabs adapter · warm voice"],
  ["00:05.618", "asset.verified", "SHA-256 84f1…c29a"],
  ["00:12.908", "run.completed", "3 assets + manifest sealed"],
];

export default function Home() {
  const [running, setRunning] = useState(false);
  const [complete, setComplete] = useState(false);
  const [step, setStep] = useState(-1);
  const [tab, setTab] = useState<"output" | "events" | "manifest">("output");
  const [brief, setBrief] = useState(
    "Launch a refillable trail bottle for urban hikers. Calm, tactile, optimistic. Deliver a 15-second social cut, hero image, and warm voiceover."
  );
  const [current, setCurrent] = useState<Provenance | null>(null);
  const [history, setHistory] = useState<Provenance[]>([]);
  const [apiOnline, setApiOnline] = useState(false);

  useEffect(() => {
    fetch(`${apiUrl}/api/generations`)
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        setApiOnline(true);
        return response.json();
      })
      .then(setHistory)
      .catch(() => setApiOnline(false));
  }, []);

  useEffect(() => {
    if (!running) return;
    if (step >= stages.length - 1) {
      const done = window.setTimeout(() => {
        setRunning(false);
        setComplete(true);
        setTab("output");
      }, 900);
      return () => window.clearTimeout(done);
    }
    const timer = window.setTimeout(() => setStep((value) => value + 1), 900);
    return () => window.clearTimeout(timer);
  }, [running, step]);

  const progress = useMemo(
    () => (complete ? 100 : Math.max(0, ((step + 1) / stages.length) * 100)),
    [complete, step]
  );

  async function runDemo(parentId?: string) {
    setComplete(false);
    setStep(-1);
    setTab("events");
    setRunning(true);
    if (apiOnline) {
      try {
        const url = parentId
          ? `${apiUrl}/api/generations/${parentId}/replay`
          : `${apiUrl}/api/generations`;
        const body = parentId ? {} : { prompt: brief, size: "1536x1024", quality: "medium" };
        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        if (!response.ok) throw new Error("Generation failed");
        const record = await response.json();
        setCurrent(record);
        setHistory((items) => [record, ...items.filter((item) => item.id !== record.id)]);
      } catch {
        setApiOnline(false);
      }
    }
  }

  return (
    <main>
      <nav className="topbar">
        <a className="brand" href="#top" aria-label="TraceFrame home">
          <span className="brand-mark">TF</span>
          <span>TRACEFRAME</span>
        </a>
        <div className="nav-links">
          <a href="#pipeline">Pipeline</a>
          <a href="#provenance">Provenance</a>
          <span className="live-pill"><i /> {apiOnline ? "API connected" : "Demo mode"}</span>
          <a className="github" href="https://github.com" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </nav>

      <section className="hero" id="top">
        <div className="eyebrow"><span>GENBLAZE × BACKBLAZE B2</span><b>01</b></div>
        <h1>GENERATE.<br /><em>PROVE.</em> REPLAY.</h1>
        <div className="hero-bottom">
          <p>
            A provenance-first media pipeline that turns one brief into
            production-ready campaign assets—then keeps every decision,
            dependency, and byte verifiable.
          </p>
          <div className="hero-stat">
            <b>01</b>
            <span>brief</span>
            <strong>→</strong>
            <b>03</b>
            <span>assets</span>
            <strong>→</strong>
            <b>01</b>
            <span>proof</span>
          </div>
        </div>
      </section>

      <section className="studio" id="pipeline">
        <div className="section-label">
          <span>LIVE STUDIO</span>
          <span>REACTIVE MULTI-PROVIDER ORCHESTRATION</span>
        </div>

        <div className="studio-grid">
          <aside className="brief-panel">
            <div className="panel-heading"><span>01</span><h2>Campaign brief</h2></div>
            <label htmlFor="brief">Describe the story you need</label>
            <textarea id="brief" value={brief} onChange={(e) => setBrief(e.target.value)} />

            <div className="field-row">
              <div><label>Format</label><button className="select-button">Social launch <span>⌄</span></button></div>
              <div><label>Duration</label><button className="select-button">15 seconds <span>⌄</span></button></div>
            </div>

            <div className="deliverables">
              <label>Deliverables</label>
              <div><button className="chip active">Key visual</button><button className="chip active">Voiceover</button><button className="chip active">Video cut</button></div>
            </div>

            <button className="run-button" onClick={() => runDemo()} disabled={running || !brief.trim()}>
              <span>{running ? "Pipeline running" : complete ? "Run again" : "Run pipeline"}</span>
              <b>{running ? `${Math.round(progress)}%` : "↗"}</b>
            </button>
            <p className="demo-note">No keys needed · seeded demo assets · real event model</p>
          </aside>

          <section className="pipeline-panel">
            <div className="panel-heading"><span>02</span><h2>Pipeline</h2><small>{running ? "RUNNING" : complete ? "COMPLETE" : "READY"}</small></div>
            <div className="progress-track"><i style={{ width: `${progress}%` }} /></div>
            <div className="stage-list">
              {stages.map((stage, index) => {
                const state = complete || index < step ? "done" : index === step ? "active" : "";
                return (
                  <div className={`stage ${state}`} key={stage.name}>
                    <span className="stage-num">{String(index + 1).padStart(2, "0")}</span>
                    <div><b>{stage.name}</b><small>{stage.provider}</small></div>
                    <span className="stage-time">{state === "active" ? "processing…" : state === "done" ? stage.time : "—"}</span>
                    <i className="stage-state">{state === "done" ? "✓" : state === "active" ? "●" : "○"}</i>
                  </div>
                );
              })}
            </div>
            <div className="resilience">
              <span>RESILIENCE</span>
              <div><b>2×</b><small>auto retry</small></div>
              <div><b>3</b><small>provider adapters</small></div>
              <div><b>100%</b><small>event replay</small></div>
            </div>
          </section>

          <section className="result-panel">
            <div className="tabs">
              <button className={tab === "output" ? "active" : ""} onClick={() => setTab("output")}>Output</button>
              <button className={tab === "events" ? "active" : ""} onClick={() => setTab("events")}>Events</button>
              <button className={tab === "manifest" ? "active" : ""} onClick={() => setTab("manifest")}>Manifest</button>
            </div>

            {tab === "output" && (
              <div className="output-view">
                <div className={`visual ${complete ? "revealed" : ""}`}>
                  <div className="sun" />
                  <div className="bottle">TRACE<br />/ 01</div>
                  <div className="visual-copy"><span>BUILT TO<br />COME BACK.</span><small>REFILL THE ROUTE</small></div>
                  {!complete && <div className="empty-state"><b>{running ? "Rendering media" : "Ready to create"}</b><span>{running ? "Watch the live events" : "Run the pipeline to generate assets"}</span></div>}
                </div>
                <div className="asset-strip">
                  <div><b>Hero image</b><small>2048×1152 · WEBP</small></div>
                  <div><b>Voice track</b><small>00:15 · MP3</small></div>
                  <div><b>Social cut</b><small>1080×1920 · MP4</small></div>
                </div>
              </div>
            )}

            {tab === "events" && (
              <div className="event-view">
                <div className="event-head"><span>EVENT STREAM</span><i className={running ? "pulse" : ""} /> <small>{running ? "LIVE" : complete ? "SEALED" : "WAITING"}</small></div>
                {events.slice(0, running ? Math.max(1, step + 2) : complete ? events.length : 2).map(([time, type, msg]) => (
                  <div className="event" key={time}><time>{time}</time><b>{type}</b><span>{msg}</span></div>
                ))}
              </div>
            )}

            {tab === "manifest" && (
              <div>
              <pre className="manifest">{`{
  "run_id": "${current?.id || "run_7F2A"}",
  "parent_run_id": ${current?.parent_id ? `"${current.parent_id}"` : "null"},
  "status": "${current?.status || (complete ? "verified" : "preview")}",
  "orchestrator": "genblaze",
  "storage": "backblaze-b2",
  "model": "${current?.model || "gpt-image-1"}",
  "manifest_sha256":
    "${current?.manifest_sha256 ? `${current.manifest_sha256.slice(0, 12)}...` : "84f1c6ab...c29a"}",
  "replayable": true
}`}</pre>
              {current && <button className="replay-button" onClick={() => runDemo(current.id)} disabled={running}>Replay this generation ↻</button>}
              </div>
            )}
          </section>
        </div>
      </section>

      <section className="proof" id="provenance">
        <div className="proof-copy">
          <div className="eyebrow dark"><span>PROVENANCE, NOT PROMISES</span><b>03</b></div>
          <h2>EVERY ASSET<br />HAS A <em>MEMORY.</em></h2>
          <p>TraceFrame stores the output and the evidence: prompts, model versions, timings, retries, parent assets, and content hashes. Rebuild the work—not the mystery.</p>
        </div>
        <div className="proof-grid">
          {history.slice(0, 4).map((record, index) => (
            <article key={record.id}>
              <span>{String(index + 1).padStart(2, "0")} · {record.id.slice(-6)}</span>
              <b>{record.parent_id ? "Replayed generation" : "Original generation"}</b>
              <p>{record.prompt.slice(0, 110)}{record.prompt.length > 110 ? "…" : ""}<br />SHA {record.asset_sha256?.slice(0, 12) || "pending"}…</p>
            </article>
          ))}
          {history.length === 0 && <>
          <article><span>01</span><b>Durable by default</b><p>Generated media and metadata land in B2 with lifecycle-aware object keys.</p></article>
          <article><span>02</span><b>Cryptographically sealed</b><p>SHA-256 manifests detect changes and connect every derivative to its source.</p></article>
          <article><span>03</span><b>Replayable pipelines</b><p>Event logs preserve the full run so teams can inspect, retry, or reproduce it.</p></article>
          <article><span>04</span><b>Provider independent</b><p>Genblaze adapters make models swappable without rewriting the product workflow.</p></article>
          </>}
        </div>
      </section>

      <footer>
        <div className="brand"><span className="brand-mark">TF</span><span>TRACEFRAME</span></div>
        <p>Built for the Backblaze Generative Media Hackathon.</p>
        <span>GENBLAZE / B2 / 2026</span>
      </footer>
    </main>
  );
}
