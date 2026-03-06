from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import numpy as np
import json
import os
import httpx
from datetime import date, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:GUlVZnKeNQoLXPbOkIqyFAEcnCMHDVSF@shuttle.proxy.rlwy.net:31411/railway"
)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TAU_FITNESS  = 45
TAU_FATIGUE  = 7
EXERCISES_FILE = "exercises.json"

USER_PROFILE = {
    "name": "Sinjin",
    "height": "6'2\"",
    "weight": "185lbs",
    "body_composition": "lean/shredded",
    "training_level": "advanced",
    "training_years": "3-7",
    "current_goal_block": "Strength — Pull & Press",
    "active_goals": ["Weighted pull-up +175lbs", "Bench press 315lbs"],
    "all_goals": [
        "Weighted pull-up +175lbs (bodyweight)",
        "Bench press 315lbs",
        "Windmill dunk",
        "405lb squat",
        "Full planche",
        "Front lever"
    ],
    "considerations": [
        "Long levers at 6'2\" — extra torque on knees, shoulders, elbows",
        "Joint sensitivity — monitor high-stress positions",
        "Advanced lifter — needs real intensity, not coddling",
        "Feedback loop — prescription should adapt based on session feel"
    ],
    "exercise_notes": {
        "Pull-Ups": "Bodyweight + added load. Track total weight. Currently working toward +175lbs added.",
        "Bench Press": "Working toward 315. Long arms = wider ROM, prioritize scapular retraction.",
        "Squat": "6'2\" with long femurs. Watch knee tracking and depth.",
        "Planche": "Skill-based, not current priority block.",
        "Front Lever": "Skill-based, not current priority block."
    }
}

# ── DB ─────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def compute_banister():
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            SELECT date, exercise_name, weight, reps
            FROM workouts WHERE weight > 0 AND reps > 0 ORDER BY date
        """)
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f"DB error in compute_banister: {e}")
        return 0, 0, []

    if not rows:
        return 0, 0, []

    import pandas as pd
    df = pd.DataFrame(rows, columns=['date','exercise_name','weight','reps'])
    df['date'] = pd.to_datetime(df['date'])
    df['estimated_1rm'] = df['weight'] * (1 + df['reps'] / 30)
    df = df.sort_values('date')
    df['max_1rm'] = df.groupby('exercise_name')['estimated_1rm'].cummax()
    df['intensity'] = df['weight'] / df['max_1rm']
    df['trimp'] = df['weight'] * df['reps'] * (df['intensity'] ** 2)

    daily = df.groupby('date')['trimp'].sum().reset_index()
    all_dates = pd.date_range(daily['date'].min(), date.today())
    daily = daily.set_index('date').reindex(all_dates, fill_value=0).reset_index()
    daily.columns = ['date', 'trimp']

    fitness, fatigue = 0.0, 0.0
    history = []
    for _, row in daily.iterrows():
        fitness = fitness * np.exp(-1 / TAU_FITNESS) + row['trimp']
        fatigue = fatigue * np.exp(-1 / TAU_FATIGUE) + row['trimp']
        history.append({
            "date":        str(row['date'].date()),
            "trimp":       round(float(row['trimp']), 1),
            "fitness":     round(fitness, 1),
            "fatigue":     round(fatigue, 1),
            "performance": round(fitness - fatigue, 1)
        })

    return fitness, fatigue, history

def get_1rms():
    try:
        conn   = get_conn()
        cur    = conn.cursor()
        cutoff = date.today() - timedelta(days=90)
        cur.execute("""
            SELECT exercise_name, MAX(weight * (1 + reps / 30.0)) AS estimated_1rm
            FROM workouts WHERE weight > 0 AND reps > 0 AND date >= %s
            GROUP BY exercise_name
        """, (cutoff,))
        rows = cur.fetchall()
        conn.close()
        return {r[0]: round(float(r[1]), 1) for r in rows}
    except Exception as e:
        print(f"DB error in get_1rms: {e}")
        return {}

def get_recent_performance(exercise_names, days=14):
    """Get last N days of performance per exercise for AI context."""
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cutoff = date.today() - timedelta(days=days)
        cur.execute("""
            SELECT exercise_name, date, MAX(weight) as max_weight, MAX(reps) as max_reps
            FROM workouts
            WHERE weight > 0 AND reps > 0 AND date >= %s
            AND exercise_name = ANY(%s)
            GROUP BY exercise_name, date
            ORDER BY exercise_name, date DESC
        """, (cutoff, exercise_names))
        rows = cur.fetchall()
        conn.close()
        result = {}
        for ex, d, w, r in rows:
            if ex not in result:
                result[ex] = []
            if len(result[ex]) < 3:
                result[ex].append({"date": str(d), "weight": w, "reps": r})
        return result
    except Exception as e:
        print(f"DB error in get_recent_performance: {e}")
        return {}

def detect_phase(fitness, fatigue):
    ratio = fatigue / fitness if fitness > 0 else 0
    if ratio > 1.3:    return "deload"
    elif ratio > 1.1:  return "peak"
    elif ratio > 0.85: return "intensification"
    else:              return "accumulation"

# ── Routes ─────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Atlas API is running"}

@app.get("/debug")
def debug():
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM workouts")
        count = cur.fetchone()[0]
        conn.close()
        return {"db_connected": True, "workout_rows": count, "db_url_prefix": DATABASE_URL[:40]}
    except Exception as e:
        return {"db_connected": False, "error": str(e), "db_url_prefix": DATABASE_URL[:40]}

@app.get("/state")
def get_state():
    fitness, fatigue, history = compute_banister()
    phase = detect_phase(fitness, fatigue)
    return {
        "fitness":     round(fitness, 1),
        "fatigue":     round(fatigue, 1),
        "performance": round(fitness - fatigue, 1),
        "phase":       phase,
        "history":     history[-90:]
    }

@app.get("/exercises")
def get_exercises():
    one_rms = get_1rms()
    try:
        with open(EXERCISES_FILE, "r") as f:
            data = json.load(f)
        for name, ex in data["exercises"].items():
            ex["estimated_1rm"] = one_rms.get(name, 0)
        return data
    except Exception as e:
        print(f"Error loading exercises: {e}")
        return {"exercises": {}, "splits": {}}

@app.get("/checkin/today")
def get_today_checkin():
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM checkins WHERE date = %s", (date.today(),))
        row = cur.fetchone()
        conn.close()
        if not row:
            return {"exists": False}
        return {"exists": True, "data": dict(row)}
    except Exception as e:
        print(f"DB error in get_today_checkin: {e}")
        return {"exists": False}

class CheckInPayload(BaseModel):
    sleep_hours:   float
    sleep_quality: float
    mood:          float
    nutrition:     float
    stress:        float
    soreness:      dict
    notes:         str = ""

@app.post("/checkin")
def submit_checkin(payload: CheckInPayload):
    avg_soreness = sum(payload.soreness.values()) / max(len(payload.soreness), 1)
    readiness = round(
        0.35 * payload.sleep_quality +
        0.30 * (1 - avg_soreness) +
        0.20 * payload.mood +
        0.15 * (1 - payload.stress), 3
    )
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO checkins (
                date, sleep_hours, sleep_quality, mood, nutrition, stress,
                avg_soreness, readiness, notes,
                soreness_quads, soreness_hamstrings, soreness_glutes,
                soreness_back, soreness_chest, soreness_shoulders,
                soreness_biceps, soreness_triceps
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (date) DO UPDATE SET
                sleep_hours   = EXCLUDED.sleep_hours,
                sleep_quality = EXCLUDED.sleep_quality,
                mood          = EXCLUDED.mood,
                nutrition     = EXCLUDED.nutrition,
                stress        = EXCLUDED.stress,
                avg_soreness  = EXCLUDED.avg_soreness,
                readiness     = EXCLUDED.readiness,
                notes         = EXCLUDED.notes,
                soreness_quads      = EXCLUDED.soreness_quads,
                soreness_hamstrings = EXCLUDED.soreness_hamstrings,
                soreness_glutes     = EXCLUDED.soreness_glutes,
                soreness_back       = EXCLUDED.soreness_back,
                soreness_chest      = EXCLUDED.soreness_chest,
                soreness_shoulders  = EXCLUDED.soreness_shoulders,
                soreness_biceps     = EXCLUDED.soreness_biceps,
                soreness_triceps    = EXCLUDED.soreness_triceps
        """, (
            date.today(),
            payload.sleep_hours, payload.sleep_quality,
            payload.mood, payload.nutrition, payload.stress,
            round(avg_soreness, 3), readiness, payload.notes,
            payload.soreness.get("quads",      0),
            payload.soreness.get("hamstrings", 0),
            payload.soreness.get("glutes",     0),
            payload.soreness.get("back",       0),
            payload.soreness.get("chest",      0),
            payload.soreness.get("shoulders",  0),
            payload.soreness.get("biceps",     0),
            payload.soreness.get("triceps",    0),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB error in submit_checkin: {e}")
    return {"readiness": readiness}

class AIPrescriptionRequest(BaseModel):
    exercises:  list
    readiness:  float
    soreness:   dict
    sleep:      float = 0.7
    mood:       float = 0.7
    nutrition:  float = 0.7
    stress:     float = 0.3

@app.post("/prescribe/ai")
async def prescribe_ai(req: AIPrescriptionRequest):
    if not ANTHROPIC_API_KEY:
        return {"error": "No API key configured"}

    fitness, fatigue, _ = compute_banister()
    phase = detect_phase(fitness, fatigue)
    one_rms = get_1rms()
    ex_names = [e["name"] for e in req.exercises]
    recent = get_recent_performance(ex_names)

    soreness_summary = ", ".join(
        f"{m}: {'mild' if v <= 0.4 else 'high'}"
        for m, v in req.soreness.items() if v > 0
    ) or "none"

    exercise_lines = []
    for ex in req.exercises:
        name = ex["name"]
        one_rm = one_rms.get(name, ex.get("oneRM"))
        note = USER_PROFILE["exercise_notes"].get(name, "")
        recent_str = ""
        if name in recent:
            recent_str = " | recent: " + ", ".join(
                f"{r['weight']}lbs×{r['reps']} ({r['date']})" for r in recent[name]
            )
        exercise_lines.append(
            f"- {name} (type: {ex.get('type','compound')}, "
            f"est. 1RM: {str(one_rm)+'lbs' if one_rm else 'unknown'}"
            f"{recent_str}"
            f"{', note: '+note if note else ''})"
        )

    prompt = f"""You are an elite strength and conditioning coach for {USER_PROFILE['name']}.

ATHLETE PROFILE:
- Height: {USER_PROFILE['height']}, Weight: {USER_PROFILE['weight']}, Composition: {USER_PROFILE['body_composition']}
- Training level: {USER_PROFILE['training_level']} ({USER_PROFILE['training_years']} years)
- Current goal block: {USER_PROFILE['current_goal_block']}
- Active goals: {', '.join(USER_PROFILE['active_goals'])}
- All goals: {', '.join(USER_PROFILE['all_goals'])}
- Considerations: {'; '.join(USER_PROFILE['considerations'])}

TODAY'S STATUS:
- Readiness: {req.readiness:.2f}/1.0 ({'HIGH' if req.readiness >= 0.75 else 'MODERATE' if req.readiness >= 0.5 else 'LOW'})
- Sleep: {round(req.sleep*10)}/10, Mood: {round(req.mood*10)}/10, Nutrition: {round(req.nutrition*10)}/10, Stress: {round(req.stress*10)}/10
- Soreness: {soreness_summary}
- Training phase: {phase.upper()}
- Fitness (long-term): {round(fitness):,} | Fatigue (short-term): {round(fatigue):,}

TODAY'S EXERCISES:
{chr(10).join(exercise_lines)}

Generate a precise, science-based prescription for this advanced athlete. Be direct — real numbers, not vague ranges unless genuinely warranted. Account for exercise-specific mechanics (pull-ups scale by total bodyweight + added load, skill work uses holds/progressions not % 1RM). If readiness is low, reduce volume but don't eliminate intensity entirely.

Respond ONLY with valid JSON, no other text:
{{
  "focus_cue": "One powerful coaching cue for today",
  "coaching_note": "2-3 sentences: context on today given readiness + phase + goals. Be direct.",
  "exercises": [
    {{
      "name": "exercise name",
      "sets": 4,
      "reps": "5",
      "load": "225lbs",
      "intensity_note": "brief rationale",
      "cue": "one technique cue specific to this athlete's body"
    }}
  ],
  "recovery_note": "one sentence if relevant, else null"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
        data = response.json()
        text = "".join(b.get("text", "") for b in data.get("content", []))
        clean = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
        result["phase"] = phase
        return result
    except Exception as e:
        print(f"AI prescription error: {e}")
        return {"error": str(e)}

class PrescriptionRequest(BaseModel):
    exercises: list
    readiness: float
    soreness:  dict

@app.post("/prescribe")
def prescribe(req: PrescriptionRequest):
    try:
        with open(EXERCISES_FILE, "r") as f:
            ex_data = json.load(f)
    except:
        ex_data = {"exercises": {}}

    one_rms      = get_1rms()
    fitness, fatigue, _ = compute_banister()
    phase        = detect_phase(fitness, fatigue)

    PHASES = {
        "accumulation":    {"intensity": 0.75, "sets": 4, "reps": 8},
        "intensification": {"intensity": 0.85, "sets": 4, "reps": 5},
        "peak":            {"intensity": 0.92, "sets": 3, "reps": 3},
        "deload":          {"intensity": 0.55, "sets": 3, "reps": 10},
    }
    phase_config = PHASES[phase]
    results      = []

    for ex_name in req.exercises:
        ex_info   = ex_data["exercises"].get(ex_name, {})
        intensity = phase_config["intensity"] * req.readiness
        ex_type   = ex_info.get("type", "compound")

        if ex_type == "compound":
            sets, reps = phase_config["sets"], phase_config["reps"]
        elif ex_type == "isolation":
            sets, reps = 3, 12
        else:
            sets, reps = 4, "max"

        sore_muscles = [m for m in ex_info.get("muscles_primary", [])
                        if req.soreness.get(m, 0) >= 0.6]
        if sore_muscles:
            intensity = round(intensity * 0.85, 3)
            sets      = max(2, sets - 1)

        one_rm = one_rms.get(ex_name)
        if ex_type in ["skill", "endurance"] or not one_rm:
            weight, pct = None, None
        else:
            weight = round((one_rm * intensity) / 2.5) * 2.5
            pct    = round(intensity * 100)

        results.append({
            "exercise":      ex_name,
            "sets":          sets,
            "reps":          reps,
            "weight":        weight,
            "intensity_pct": pct,
            "estimated_1rm": round(one_rm, 1) if one_rm else None,
            "sore_warning":  ", ".join(sore_muscles) if sore_muscles else None,
            "type":          ex_type
        })

    return {"phase": phase, "prescriptions": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
