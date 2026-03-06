import { useState, useEffect } from "react";

const API = "https://atlas-production-d795.up.railway.app";

const STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500&family=Barlow:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #080810;
    --bg2:      #0f0f1a;
    --bg3:      #16162a;
    --border:   #1e1e3a;
    --accent:   #00e5ff;
    --accent2:  #7b2fff;
    --green:    #00ff87;
    --red:      #ff3d5a;
    --yellow:   #ffd60a;
    --text:     #e8e8f0;
    --muted:    #5a5a7a;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-mono:    'IBM Plex Mono', monospace;
    --font-body:    'Barlow', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    min-height: 100vh;
    overflow-x: hidden;
  }

  .app {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 24px 80px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 28px 0 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }
  .logo {
    font-family: var(--font-display);
    font-size: 28px;
    font-weight: 700;
    letter-spacing: 6px;
    text-transform: uppercase;
    color: var(--accent);
    text-shadow: 0 0 30px rgba(0,229,255,0.3);
  }
  .logo span { color: var(--muted); font-weight: 300; }
  .date-badge {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 2px;
  }

  .nav {
    display: flex;
    gap: 4px;
    margin-bottom: 32px;
  }
  .nav-btn {
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 10px 20px;
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    cursor: pointer;
    transition: all 0.15s;
  }
  .nav-btn:hover { border-color: var(--accent); color: var(--accent); }
  .nav-btn.active {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--bg);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 28px;
  }
  @media (max-width: 700px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

  .stat-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 20px;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .stat-card.blue::before   { background: var(--accent); }
  .stat-card.purple::before { background: var(--accent2); }
  .stat-card.green::before  { background: var(--green); }
  .stat-card.yellow::before { background: var(--yellow); }

  .stat-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
  }
  .stat-value {
    font-family: var(--font-display);
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 4px;
  }
  .stat-card.blue   .stat-value { color: var(--accent); }
  .stat-card.purple .stat-value { color: var(--accent2); }
  .stat-card.green  .stat-value { color: var(--green); }
  .stat-card.yellow .stat-value { color: var(--yellow); }

  .stat-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--muted);
  }

  .phase-banner {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 28px;
  }
  .phase-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 3px;
    color: var(--muted);
    text-transform: uppercase;
  }
  .phase-name {
    font-family: var(--font-display);
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
  }
  .phase-desc {
    font-size: 13px;
    color: var(--muted);
    max-width: 400px;
    line-height: 1.5;
  }

  .section-title {
    font-family: var(--font-display);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .checkin-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 600px) { .checkin-grid { grid-template-columns: 1fr; } }

  .field {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 16px;
  }
  .field-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
  }
  .field-label span { color: var(--accent); font-size: 12px; }
  .slider {
    width: 100%;
    -webkit-appearance: none;
    appearance: none;
    height: 3px;
    background: var(--border);
    outline: none;
    cursor: pointer;
  }
  .slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 14px; height: 14px;
    background: var(--accent);
    cursor: pointer;
    border-radius: 0;
  }

  .soreness-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 24px;
  }
  @media (max-width: 600px) { .soreness-grid { grid-template-columns: repeat(2, 1fr); } }

  .muscle-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 12px;
    cursor: pointer;
    transition: all 0.15s;
    text-align: center;
  }
  .muscle-card:hover { border-color: var(--accent); }
  .muscle-card.sore-low  { border-color: var(--yellow); }
  .muscle-card.sore-high { border-color: var(--red); }
  .muscle-name {
    font-family: var(--font-display);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text);
    margin-bottom: 8px;
  }
  .muscle-level { font-family: var(--font-mono); font-size: 18px; font-weight: 500; }
  .muscle-card.sore-low  .muscle-level { color: var(--yellow); }
  .muscle-card.sore-high .muscle-level { color: var(--red); }
  .muscle-card:not(.sore-low):not(.sore-high) .muscle-level { color: var(--green); }

  .notes-field {
    width: 100%;
    background: var(--bg2);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: var(--font-body);
    font-size: 14px;
    padding: 14px 16px;
    resize: vertical;
    min-height: 80px;
    outline: none;
    margin-bottom: 20px;
  }
  .notes-field::placeholder { color: var(--muted); }
  .notes-field:focus { border-color: var(--accent); }

  .readiness-result {
    background: var(--bg3);
    border: 1px solid var(--border);
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;
  }
  .readiness-score {
    font-family: var(--font-display);
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    min-width: 120px;
  }
  .readiness-info .status {
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
  }
  .readiness-info .detail { font-size: 13px; color: var(--muted); line-height: 1.6; }

  .split-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 28px;
  }
  @media (max-width: 600px) { .split-grid { grid-template-columns: 1fr; } }

  .split-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 20px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .split-card:hover { border-color: var(--accent); }
  .split-card.selected { border-color: var(--accent); background: rgba(0,229,255,0.05); }
  .split-card-name {
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text);
    margin-bottom: 10px;
  }
  .split-card.selected .split-card-name { color: var(--accent); }
  .split-exercises { font-size: 12px; color: var(--muted); line-height: 1.8; }

  .exercise-picker {
    background: var(--bg2);
    border: 1px solid var(--border);
    padding: 20px;
    margin-bottom: 24px;
  }
  .exercise-list { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
  .exercise-toggle {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: all 0.1s;
  }
  .exercise-toggle:hover { background: var(--bg3); }
  .exercise-toggle.checked { border-color: var(--border); background: var(--bg3); }
  .toggle-box {
    width: 16px; height: 16px;
    border: 1px solid var(--muted);
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px;
    color: var(--accent);
  }
  .exercise-toggle.checked .toggle-box { border-color: var(--accent); background: rgba(0,229,255,0.1); }
  .exercise-toggle-name { font-family: var(--font-body); font-size: 14px; color: var(--text); }
  .exercise-type-badge {
    margin-left: auto;
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--muted);
    padding: 2px 6px;
    border: 1px solid var(--border);
  }

  .prescription-header {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent);
    padding: 20px 24px;
    margin-bottom: 16px;
  }
  .prescription-title {
    font-family: var(--font-display);
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 4px;
  }
  .prescription-meta { font-family: var(--font-mono); font-size: 11px; color: var(--muted); letter-spacing: 1px; }

  .exercise-row {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid transparent;
    padding: 18px 20px;
    margin-bottom: 8px;
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 16px;
    transition: border-color 0.15s;
  }
  .exercise-row:hover { border-left-color: var(--accent); }
  .exercise-row.has-warning { border-left-color: var(--yellow); }
  .ex-name { font-family: var(--font-display); font-size: 17px; font-weight: 600; letter-spacing: 1px; color: var(--text); margin-bottom: 4px; }
  .ex-prescription { font-family: var(--font-mono); font-size: 12px; color: var(--accent); margin-bottom: 4px; }
  .ex-warning { font-size: 11px; color: var(--yellow); margin-top: 4px; }
  .ex-1rm { text-align: right; }
  .ex-1rm-value { font-family: var(--font-display); font-size: 28px; font-weight: 700; color: var(--text); line-height: 1; }
  .ex-1rm-label { font-family: var(--font-mono); font-size: 9px; letter-spacing: 2px; color: var(--muted); text-transform: uppercase; }

  .btn {
    font-family: var(--font-display);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    padding: 14px 32px;
    border: none;
    cursor: pointer;
    transition: all 0.15s;
    display: inline-block;
  }
  .btn-primary { background: var(--accent); color: var(--bg); }
  .btn-primary:hover { background: #33eeff; box-shadow: 0 0 20px rgba(0,229,255,0.3); }
  .btn-secondary { background: transparent; border: 1px solid var(--accent); color: var(--accent); }
  .btn-secondary:hover { background: rgba(0,229,255,0.1); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .bar-chart { background: var(--bg2); border: 1px solid var(--border); padding: 20px; margin-bottom: 28px; }
  .bars { display: flex; align-items: flex-end; gap: 3px; height: 80px; margin-top: 12px; }
  .bar { flex: 1; background: var(--accent); opacity: 0.6; transition: opacity 0.1s; min-height: 2px; }
  .bar:hover { opacity: 1; }

  .loading { font-family: var(--font-mono); font-size: 11px; color: var(--muted); letter-spacing: 2px; padding: 8px 0; }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); }
`;

const MUSCLES = ["quads","hamstrings","glutes","back","chest","shoulders","biceps","triceps"];

// ── Helpers ──────────────────────────────────────────────────────────────────
function calcReadiness(checkin) {
  const { sleep, soreness, mood, nutrition, stress } = checkin;
  const avgSoreness = Object.values(soreness).reduce((a,b) => a+b, 0) / MUSCLES.length;
  return Math.round((0.35*sleep + 0.30*(1-avgSoreness) + 0.20*mood + 0.15*(1-stress)) * 100) / 100;
}

function getReadinessColor(r) {
  if (r >= 0.75) return "var(--green)";
  if (r >= 0.50) return "var(--yellow)";
  return "var(--red)";
}

function getReadinessStatus(r) {
  if (r >= 0.75) return { label: "HIGH — Push today", detail: "Your body is ready for full load. Today is a good day to push intensity." };
  if (r >= 0.50) return { label: "MODERATE — Train smart", detail: "Sub-optimal recovery. Hit prescribed weights but don't push beyond them." };
  return { label: "LOW — Recovery focus", detail: "Significant fatigue detected. Reduce load 20-30% and prioritize movement quality." };
}

function prescribe(exercise, readiness, soreness) {
  const intensity = 0.75 * readiness;
  const soreCheck = exercise.type === "compound" ? MUSCLES.filter(m => soreness[m] >= 0.6) : [];
  const isSore = soreCheck.length > 0;
  const adjIntensity = isSore ? intensity * 0.85 : intensity;
  if (exercise.type === "skill") return { sets: 4, reps: "max", weight: null, note: "bodyweight — focus on form" };
  if (!exercise.oneRM) return { sets: exercise.type === "isolation" ? 3 : 4, reps: exercise.type === "isolation" ? 12 : 8, weight: null, note: "no data — start light" };
  const weight = Math.round((exercise.oneRM * adjIntensity) / 2.5) * 2.5;
  const sets = isSore ? Math.max(2, (exercise.type === "isolation" ? 3 : 4) - 1) : (exercise.type === "isolation" ? 3 : 4);
  const reps = exercise.type === "isolation" ? 12 : 8;
  return { sets, reps, weight, pct: Math.round(adjIntensity * 100), warning: isSore ? "sore — load reduced 15%" : null };
}

// ── Components ───────────────────────────────────────────────────────────────
function Dashboard({ checkin, onNav, serverState }) {
  const readiness = checkin ? calcReadiness(checkin) : null;

  const fitness     = serverState ? serverState.fitness     : null;
  const fatigue     = serverState ? serverState.fatigue     : null;
  const performance = serverState ? serverState.performance : null;
  const phase       = serverState ? serverState.phase       : null;

  const history = serverState ? serverState.history.slice(-28) : [];
  const maxTrimp = history.length ? Math.max(...history.map(h => h.trimp), 1) : 1;

  const phaseDescs = {
    accumulation:    "Build volume and base strength. Focus on consistent load progression across all movements.",
    intensification: "Increasing intensity. Volume drops, weight goes up. Stay focused on technique.",
    peak:            "Fatigue is clearing. Performance window is open — push for PRs this week.",
    deload:          "Recovery phase. Reduce load and let fitness consolidate. You'll come back stronger.",
  };

  return (
    <div>
      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-label">Fitness Score</div>
          <div className="stat-value">{fitness ? (fitness/1000).toFixed(1)+'K' : '—'}</div>
          <div className="stat-sub">long-term adaptation</div>
        </div>
        <div className="stat-card purple">
          <div className="stat-label">Fatigue Score</div>
          <div className="stat-value">{fatigue ? (fatigue/1000).toFixed(1)+'K' : '—'}</div>
          <div className="stat-sub">short-term stress</div>
        </div>
        <div className="stat-card green">
          <div className="stat-label">Performance</div>
          <div className="stat-value">{performance ? (performance/1000).toFixed(1)+'K' : '—'}</div>
          <div className="stat-sub">fitness − fatigue</div>
        </div>
        <div className="stat-card yellow">
          <div className="stat-label">Readiness</div>
          <div className="stat-value" style={{color: readiness ? getReadinessColor(readiness) : 'var(--muted)'}}>
            {readiness ? readiness.toFixed(2) : "—"}
          </div>
          <div className="stat-sub">{readiness ? getReadinessStatus(readiness).label.split("—")[0].trim() : "check in first"}</div>
        </div>
      </div>

      <div className="phase-banner">
        <div>
          <div className="phase-label">Current Phase</div>
          <div className="phase-name">{phase ? phase.toUpperCase() : '—'}</div>
        </div>
        <div className="phase-desc">{phase ? phaseDescs[phase] : 'Loading...'}</div>
      </div>

      <div className="section-title">28-Day Load History</div>
      <div className="bar-chart">
        <div style={{fontFamily:"var(--font-mono)", fontSize:"10px", color:"var(--muted)", letterSpacing:"2px", marginBottom:"4px"}}>
          TRAINING IMPULSE (TRIMP) — LAST 28 DAYS
        </div>
        {history.length === 0 && <div className="loading">LOADING DATA...</div>}
        <div className="bars">
          {history.map((h, i) => (
            <div key={i} className="bar"
              style={{height: `${Math.max((h.trimp / maxTrimp) * 100, 2)}%`}}
              title={`${h.date}: ${h.trimp}`} />
          ))}
        </div>
      </div>

      <div style={{display:"flex", gap:"12px", flexWrap:"wrap"}}>
        {!checkin && <button className="btn btn-primary" onClick={() => onNav("checkin")}>Morning Check-in</button>}
        {checkin  && <button className="btn btn-primary" onClick={() => onNav("workout")}>Get Today's Prescription</button>}
        {checkin  && <button className="btn btn-secondary" onClick={() => onNav("checkin")}>Edit Check-in</button>}
      </div>
    </div>
  );
}

function CheckIn({ onComplete }) {
  const [vals, setVals] = useState({
    sleep: 0.7, mood: 0.7, nutrition: 0.7, stress: 0.3,
    soreness: Object.fromEntries(MUSCLES.map(m => [m, 0]))
  });
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [saving, setSaving] = useState(false);

  const readiness = calcReadiness(vals);
  const status = getReadinessStatus(readiness);

  const setVal = (k, v) => setVals(prev => ({...prev, [k]: v}));
  const cycleSoreness = (m) => {
    const cur = vals.soreness[m];
    const next = cur === 0 ? 0.4 : cur === 0.4 ? 0.8 : 0;
    setVals(prev => ({...prev, soreness: {...prev.soreness, [m]: next}}));
  };

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/checkin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sleep_hours:   vals.sleep * 10,
          sleep_quality: vals.sleep,
          mood:          vals.mood,
          nutrition:     vals.nutrition,
          stress:        vals.stress,
          soreness:      vals.soreness,
          notes
        })
      });
    } catch(e) {
      console.log("Server save failed, continuing with local data");
    }
    setSaving(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div>
        <div className="readiness-result">
          <div className="readiness-score" style={{color: getReadinessColor(readiness)}}>
            {readiness.toFixed(2)}
          </div>
          <div className="readiness-info">
            <div className="status" style={{color: getReadinessColor(readiness)}}>{status.label}</div>
            <div className="detail">{status.detail}</div>
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => onComplete(vals)}>
          Get Today's Prescription →
        </button>
      </div>
    );
  }

  const SliderField = ({ label, key_, val }) => (
    <div className="field">
      <div className="field-label">{label}<span>{Math.round(val * 10)}/10</span></div>
      <input type="range" className="slider" min="0" max="1" step="0.1"
        value={val} onChange={e => setVal(key_, parseFloat(e.target.value))} />
    </div>
  );

  return (
    <div>
      <div className="section-title">Daily Vitals</div>
      <div className="checkin-grid">
        <SliderField label="Sleep Quality" key_="sleep"     val={vals.sleep} />
        <SliderField label="Mood / Mental" key_="mood"      val={vals.mood} />
        <SliderField label="Nutrition"     key_="nutrition" val={vals.nutrition} />
        <SliderField label="Stress Level"  key_="stress"    val={vals.stress} />
      </div>

      <div className="section-title">Muscle Soreness — tap to cycle</div>
      <div className="soreness-grid">
        {MUSCLES.map(m => {
          const v = vals.soreness[m];
          const cls = v === 0 ? "" : v <= 0.4 ? "sore-low" : "sore-high";
          const label = v === 0 ? "FRESH" : v <= 0.4 ? "MILD" : "SORE";
          return (
            <div key={m} className={`muscle-card ${cls}`} onClick={() => cycleSoreness(m)}>
              <div className="muscle-name">{m}</div>
              <div className="muscle-level">{label}</div>
            </div>
          );
        })}
      </div>

      <div className="section-title">Notes</div>
      <textarea className="notes-field"
        placeholder="How are you feeling? Anything worth noting — sleep quality, stress, diet..."
        value={notes} onChange={e => setNotes(e.target.value)} />

      <div style={{display:"flex", alignItems:"center", gap:"16px", flexWrap:"wrap"}}>
        <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
          {saving ? "Saving..." : "Calculate Readiness"}
        </button>
        <div style={{fontFamily:"var(--font-mono)", fontSize:"11px", color:"var(--muted)"}}>
          Live preview: <span style={{color: getReadinessColor(readiness)}}>{readiness.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

function WorkoutSelect({ checkin, onSelect, serverExercises }) {
  const [selected, setSelected] = useState(null);
  const [picked, setPicked] = useState({});

  const splits = serverExercises ? serverExercises.splits.sinjin : null;
  const exerciseDb = serverExercises ? serverExercises.exercises : {};

  const handleSelect = (name) => {
    setSelected(name);
    const exs = splits[name];
    setPicked(Object.fromEntries(exs.map(e => [e, true])));
  };

  const toggleEx = (name) => setPicked(prev => ({...prev, [name]: !prev[name]}));

  if (!splits) return <div className="loading">LOADING EXERCISE DATA...</div>;

  return (
    <div>
      <div className="section-title">Select Today's Split</div>
      <div className="split-grid">
        {Object.entries(splits).map(([name, exs]) => (
          <div key={name} className={`split-card ${selected === name ? 'selected' : ''}`}
            onClick={() => handleSelect(name)}>
            <div className="split-card-name">{name}</div>
            <div className="split-exercises">
              {exs.slice(0,4).join(" · ")}
              {exs.length > 4 && ` +${exs.length-4} more`}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <>
          <div className="section-title">Select Today's Exercises</div>
          <div className="exercise-picker">
            <div style={{fontFamily:"var(--font-mono)", fontSize:"10px", color:"var(--muted)", letterSpacing:"2px", marginBottom:"4px"}}>
              TAP TO TOGGLE — {Object.values(picked).filter(Boolean).length} SELECTED
            </div>
            <div className="exercise-list">
              {splits[selected].map(exName => {
                const exInfo = exerciseDb[exName] || {};
                return (
                  <div key={exName} className={`exercise-toggle ${picked[exName] ? 'checked' : ''}`}
                    onClick={() => toggleEx(exName)}>
                    <div className="toggle-box">{picked[exName] ? "✓" : ""}</div>
                    <div className="exercise-toggle-name">{exName}</div>
                    <div className="exercise-type-badge">{exInfo.type || 'compound'}</div>
                  </div>
                );
              })}
            </div>
          </div>
          <button className="btn btn-primary"
            disabled={Object.values(picked).filter(Boolean).length === 0}
            onClick={() => {
              const chosen = splits[selected]
                .filter(e => picked[e])
                .map(e => ({
                  name: e,
                  type: exerciseDb[e]?.type || 'compound',
                  oneRM: exerciseDb[e]?.estimated_1rm || null
                }));
              onSelect(selected, chosen);
            }}>
            Generate Prescription →
          </button>
        </>
      )}
    </div>
  );
}

function Prescription({ workout, exercises, checkin, serverState }) {
  const readiness = calcReadiness(checkin);
  const status = getReadinessStatus(readiness);
  const phase = serverState ? serverState.phase : "accumulation";

  return (
    <div>
      <div className="prescription-header">
        <div className="prescription-title">{workout}</div>
        <div className="prescription-meta">
          {new Date().toDateString().toUpperCase()} &nbsp;·&nbsp;
          READINESS {readiness.toFixed(2)} &nbsp;·&nbsp;
          PHASE: {phase.toUpperCase()}
        </div>
      </div>

      <div style={{
        background: "var(--bg2)", border: "1px solid var(--border)",
        borderLeft: `3px solid ${getReadinessColor(readiness)}`,
        padding: "14px 20px", marginBottom: "20px",
        fontFamily: "var(--font-mono)", fontSize: "12px",
        color: getReadinessColor(readiness)
      }}>
        {status.label} — {status.detail}
      </div>

      <div className="section-title">Exercise Prescription</div>

      {exercises.map(ex => {
        const p = prescribe(ex, readiness, checkin.soreness);
        return (
          <div key={ex.name} className={`exercise-row ${p.warning ? 'has-warning' : ''}`}>
            <div>
              <div className="ex-name">{ex.name}</div>
              {p.weight ? (
                <div className="ex-prescription">{p.sets} sets × {p.reps} reps @ {p.weight}lbs ({p.pct}% 1RM)</div>
              ) : (
                <div className="ex-prescription">{p.sets} sets × {p.reps} — {p.note}</div>
              )}
              {p.warning && <div className="ex-warning">⚠ {p.warning}</div>}
            </div>
            {ex.oneRM ? (
              <div className="ex-1rm">
                <div className="ex-1rm-value">{ex.oneRM}</div>
                <div className="ex-1rm-label">est. 1rm</div>
              </div>
            ) : null}
          </div>
        );
      })}

      <div style={{marginTop: "24px", display:"flex", gap:"12px"}}>
        <button className="btn btn-secondary" onClick={() => window.location.reload()}>New Day</button>
      </div>
    </div>
  );
}

// ── App Shell ────────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView]           = useState("dashboard");
  const [checkin, setCheckin]     = useState(null);
  const [workout, setWorkout]     = useState(null);
  const [exercises, setExes]      = useState([]);
  const [serverState, setServerState]         = useState(null);
  const [serverExercises, setServerExercises] = useState(null);

  useEffect(() => {
    fetch(`${API}/state`)
      .then(r => r.json())
      .then(data => setServerState(data))
      .catch(() => console.log("Could not load server state"));

    fetch(`${API}/exercises`)
      .then(r => r.json())
      .then(data => setServerExercises(data))
      .catch(() => console.log("Could not load exercises"));
  }, []);

  const today = new Date().toLocaleDateString('en-US', {
    weekday:'long', month:'long', day:'numeric', year:'numeric'
  });

  const handleCheckin = (data) => { setCheckin(data); setView("workout"); };
  const handleWorkout = (name, exs) => { setWorkout(name); setExes(exs); setView("prescription"); };

  const VIEWS  = ["dashboard","checkin","workout","prescription"];
  const LABELS = ["Dashboard","Check-in","Workout","Prescription"];

  return (
    <>
      <style>{STYLE}</style>
      <div className="app">
        <div className="header">
          <div className="logo">ATL<span>A</span>S</div>
          <div className="date-badge">{today.toUpperCase()}</div>
        </div>

        <div className="nav">
          {VIEWS.map((v, i) => (
            <button key={v} className={`nav-btn ${view === v ? 'active' : ''}`} onClick={() => setView(v)}>
              {LABELS[i]}
            </button>
          ))}
        </div>

        {view === "dashboard" && (
          <Dashboard checkin={checkin} onNav={setView} serverState={serverState} />
        )}
        {view === "checkin" && (
          <CheckIn onComplete={handleCheckin} />
        )}
        {view === "workout" && checkin && (
          <WorkoutSelect checkin={checkin} onSelect={handleWorkout} serverExercises={serverExercises} />
        )}
        {view === "workout" && !checkin && (
          <div style={{fontFamily:"var(--font-mono)", color:"var(--muted)", padding:"40px 0"}}>
            Complete your morning check-in first.
            <br/><br/>
            <button className="btn btn-primary" onClick={() => setView("checkin")}>Go to Check-in</button>
          </div>
        )}
        {view === "prescription" && checkin && workout && (
          <Prescription workout={workout} exercises={exercises} checkin={checkin} serverState={serverState} />
        )}
      </div>
    </>
  );
}