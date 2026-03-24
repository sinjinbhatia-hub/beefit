from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import numpy as np
import json
import os
import httpx
from datetime import date, timedelta
from collections import defaultdict
from typing import Optional
import jwt as pyjwt

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("SUPABASE_URL", os.environ.get("DATABASE_URL", ""))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TAU_FITNESS  = 45
TAU_FATIGUE  = 7
EXERCISES_FILE = "exercises.json"

# ── User Profile ─────────────────────────────────────────────────────────────
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
        "Bench Press (Barbell)": "Working toward 315. Long arms = wider ROM, prioritize scapular retraction.",
        "Squat (Barbell)": "6'2\" with long femurs. Watch knee tracking and depth.",
        "Planche": "Skill-based, not current priority block.",
        "Front Lever": "Skill-based, not current priority block."
    }
}

# ── Coaching Knowledge Base ───────────────────────────────────────────────────
COACHING_KNOWLEDGE = """
=== ATLAS COACHING KNOWLEDGE BASE ===

── TRAINING METHODOLOGY ──────────────────────────────────────────────────────

TOP SET + BACKOFF SETS (athlete's current primary method):
- The athlete performs a heavy top set (1-5 reps at high effort), then drops weight for backoff sets at 85-95% of the top set.
- Example: Warmups → top set 225x3 → backoffs 3x5 @ 195-205lbs. This is deliberate, correct programming.
- The TOP SET is a performance/skill practice under near-max load. BACKOFF SETS are the primary training stimulus.
- NEVER treat the top set as "the training weight" for volume work. Backoffs = working weight.
- Progressive overload signal: top set weight increases session to session (e.g. 215→220→225). This is strength progress even if reps stay the same.
- When prescribing this pattern: give a top set target AND separate backoff sets at 88-92% of top set.
- This method is used in Juggernaut Method, 5/3/1, Renaissance Periodization, and many advanced strength programs.

STRAIGHT SETS:
- All sets at the same weight. E.g. 4x5 @ 210lbs. Simple and effective.
- Progression: +2.5-5lbs upper / +5-10lbs lower each session or week.

WAVE LOADING:
- Sets increase in weight across the session. 135x5, 185x3, 205x2, 225x1. Heaviest set is the top wave.
- Progress by raising the top of the wave over time.

REVERSE PYRAMID:
- Heaviest set first when freshest, then reduce weight and increase reps.
- E.g. 225x3, 210x5, 195x8. Good for maximizing heavy effort while still accumulating volume.

RPE / RIR:
- RPE 10 = max effort, no reps left. RPE 9 = 1 rep left. RPE 8 = 2 reps left.
- RIR 0 = failure. RIR 1 = 1 rep left. RIR 2 = 2 reps left.
- Target RIR for strength work: 1-2. Never 0 unless deliberate testing.
- RIR fluctuates with fatigue — same weight will feel harder on set 4 than set 1.

AMRAP (As Many Reps As Possible):
- Performed at end of main work, or as a progress test.
- Use AMRAP result to project 1RM and plan next cycle weight.

PERIODIZATION:
- Linear: Weight increases every session. Beginner-intermediate.
- Undulating (DUP): Rotate rep ranges across sessions (e.g. heavy/moderate/light days). Intermediate-advanced.
- Block: Accumulation → Intensification → Peak → Deload. Used in this app via Banister model.
- Conjugate: Multiple qualities trained simultaneously (maximal effort + dynamic effort). Advanced powerlifters.

BANISTER MODEL (in use):
- Fitness = long-term positive adaptation (tau = 45 days, builds slowly)
- Fatigue = short-term negative adaptation (tau = 7 days, dissipates quickly)
- Performance = Fitness minus Fatigue
- Phase determination from fatigue/fitness ratio:
  - Below 0.85: Accumulation — build volume, 75-82% 1RM, 3-5 sets of 6-10 reps
  - 0.85 to 1.1: Intensification — increase load, reduce volume, 82-90% 1RM, 3-5 sets of 3-6 reps
  - 1.1 to 1.3: Peak — low volume, very high intensity, 90-97% 1RM, 2-3 sets of 1-3 reps
  - Above 1.3: Deload — mandatory recovery, 50-60% 1RM, 2-3 sets of 8-10 reps

── READING TRAINING HISTORY ──────────────────────────────────────────────────

HOW TO DETECT TRAINING PATTERNS from raw set data:
- top_set_backoff: Highest weight set is significantly heavier than subsequent sets. Subsequent sets cluster at lower, similar weights. Warmup ramps visible at start.
- straight_sets: All working sets same weight ±5lbs, similar reps per set.
- pyramid: Weight increases set to set throughout. Each set heavier than last.
- reverse_pyramid: First working set is heaviest, then decreasing weight.
- mixed: Variable weights without clear pattern.

PROGRESS SIGNALS:
- Top set increased vs prior session → direct strength progress
- Backoff weight or reps increased → volume quality improving
- More total reps at same weight → hypertrophy/endurance improving
- Same reps at higher weight with lower RIR → strength improving
- Consistent backoff weight with more sets completed → work capacity improving

FATIGUE / OVERREACHING SIGNALS:
- Top set weight decreased from last session despite adequate rest
- More reps missed or RIR lower than expected on backoffs
- Reps dropping across sets within session (e.g. 5, 4, 3 when prescribed 5,5,5)
- Consecutive sessions with decreasing performance

── LOAD PRESCRIPTION SCIENCE ────────────────────────────────────────────────

1RM ESTIMATION (Epley formula, used in this app):
- estimated_1rm = weight x (1 + reps/30)
- Accurate for 1-8 rep range. Overestimates for sets of 10+ reps.
- For 1-2 rep sets, treat as close to true 1RM.

INTENSITY ZONES:
- Below 60% 1RM: Warm-up, technique work, conditioning
- 60-70%: Hypertrophy-endurance, higher reps (15-25)
- 70-80%: Hypertrophy-strength, moderate reps (8-15)
- 80-90%: Strength, low reps (3-8)
- 90-97%: Maximal strength, very low reps (1-3)
- 97%+: Near-maximal or true max effort, singles only

WORKING WEIGHT SELECTION:
- For top_set_backoff pattern: base the top set on recent top set +2.5-5lbs if prior session went well (RIR 1-2 or better).
- Backoffs should be 88-92% of today's top set prescription.
- NEVER prescribe multiple sets at a weight the athlete only hit for a single in their last session. That was a max effort single, not a working weight.
- Small progressive jumps only: compounds +2.5-5lbs/session, isolations +2.5lbs/session.

VOLUME LANDMARKS (weekly sets per muscle group):
- Maintenance: 6-8 sets/week
- Minimum effective dose: 10-12 sets/week
- Hypertrophy range: 12-20 sets/week
- Maximum recoverable volume: 20-25 sets/week (individual variation)

FATIGUE MANAGEMENT:
- Heavy compounds: 72hr minimum recovery
- Moderate compounds: 48hr
- Isolation/accessories: 24-48hr
- CNS-intensive (heavy singles, max effort work): 72-96hr
- Deload frequency: Every 4-8 weeks based on accumulated fatigue

── LONG-LEVER ATHLETE SPECIFICS (6'2") ─────────────────────────────────────

Physics: Longer limbs = longer moment arms = more torque on joints at same absolute load.
This means strength progress may be slower than average, and joint stress higher per pound lifted.

BENCH PRESS:
- Longer ROM due to longer arms. Significantly more stress at the bottom of the press.
- Scapular retraction and depression essential — protects the AC joint and shoulder capsule.
- Slightly wider grip shortens effective ROM. Legal to 81cm mark.
- Elbows at 45-75 degrees — not flared out wide, not tucked ultra-tight.
- Conservative loading on accessory chest work — pec tears are more common with long arms.

SQUAT:
- Long femurs force forward torso lean regardless of shoe or bar position.
- High bar: More upright torso but more knee stress and forward lean required.
- Low bar: Shifts stress toward hips and back, shorter effective ROM.
- Box squat: Excellent tool for learning depth and preventing forward collapse.
- Watch for knee cave (valgus collapse) under fatigue — common with long femurs.
- Tempo squats (3-1-1) build positional strength out of the hole.

DEADLIFT:
- Long torso + long legs creates challenging neutral spine at bar contact.
- Conventional stance may require very low hips and significant reach.
- Sumo stance often more biomechanically efficient for tall athletes — shorter ROM.
- Romanian DL: Long hamstrings = excellent stretch stimulus even with moderate weight.

PULL-UPS / VERTICAL PULLING:
- Long arms = excellent lat stretch at bottom — advantage for ROM and stimulus.
- More bicep tendon stress at full extension dead hang.
- Avoid ballistic kipping or dead hang drop-offs — tendon stress risk.
- Track as bodyweight + added load. At 185lbs, "+45lbs" = 230lbs total.
- Progress in 2.5-5lb increments on added load.

OVERHEAD PRESS:
- Long bar path due to long arms. More shoulder stability demanded throughout.
- Seated press reduces lower back fatigue and core variable.
- Dumbbell press allows natural arm path — often safer for shoulder health.
- Conservative loading — never push OHP to failure due to shoulder impingement risk.

── PROGRESSIVE OVERLOAD STRATEGIES ─────────────────────────────────────────

LOAD PROGRESSION:
- Novice (under 1yr): Add weight every session (5lbs upper body, 10lbs lower body).
- Intermediate (1-3yr): Add weight every week.
- Advanced (3yr+): Add weight every mesocycle (4-8 weeks) or use top-set microloading.
- For this athlete: top set increases of 2.5-5lbs every 1-2 sessions when hitting target RIR.

VOLUME PROGRESSION:
- Add 1 set per primary exercise per week across a mesocycle.
- At end of mesocycle: deload resets volume, begin next block with slightly higher weight.

TECHNIQUE PROGRESSION:
- Before increasing load, ensure movement quality. Tempo work reveals positional weaknesses.
- If form breaks down on backoffs, reduce weight rather than grinding ugly reps.

── SPORT-SPECIFIC PROGRAMMING ───────────────────────────────────────────────

POWERLIFTING (squat, bench, deadlift maxes):
- Specificity: Practice competition lifts with competition-legal technique.
- Peaking: 3-6 week peak phase. Volume drops sharply, intensity rises.
- Competition attempts: opener 90-92% projected max, second 95-97%, third = record attempt.

BASKETBALL / ATHLETIC / JUMPING (relevant for windmill dunk goal):
- Vertical jump = rate of force development (RFD) + relative strength + reactive strength.
- Plyometrics: Depth jumps, box jumps, bounds — develop RFD and stiffness.
- Strength foundation: Squat and hip hinge are primary drivers of vertical.
- Sprint mechanics: builds ankle stiffness and ground contact efficiency.
- Approach mechanics for dunking: horizontal velocity converts to vertical through hip and ankle drive.
- Relative strength matters — adding lean mass without excessive weight gain is key.

CALISTHENICS / GYMNASTICS STRENGTH (planche, front lever goals):
- Straight-arm strength is neurologically distinct from bent-arm compound lifting.
- Cannot be directly trained with barbell work — requires specific progressions.
- Planche progressions: tuck → advanced tuck → straddle → full.
  - Key muscles: anterior deltoid (straight arm), serratus anterior, core.
  - Train with planche lean, planche push-up negatives, band-assisted holds.
- Front lever progressions: tuck → one-leg → straddle → full.
  - Key muscles: lats, teres major, rear delt, core.
  - Train with Australian pull-ups, tuck FL holds, one-arm negatives.
- Both require 48-72hr recovery due to extreme isometric demands.
- Cannot be rushed — connective tissue adaptation is the limiting factor.

HYPERTROPHY FOCUS:
- Primary drivers: mechanical tension, metabolic stress, muscle damage.
- Volume is king — 12-20 sets per muscle per week in hypertrophy range.
- Rep range 8-15 most effective across most muscles.
- Mind-muscle connection and controlled eccentrics increase stimulus per set.

── RECOVERY SCIENCE ─────────────────────────────────────────────────────────

SLEEP: Most critical recovery factor. Under 7 hours = measurable performance reduction.
NUTRITION: Protein synthesis requires 0.7-1g protein/lb bodyweight. Post-workout carbohydrates restore glycogen.
STRESS: Psychological stress elevates cortisol, which competes with anabolic hormones. High stress = conservative prescription.
SORENESS: DOMS peaks 24-48hr post session. Training through mild soreness is acceptable. Severe soreness = reduce volume 30-40%.

READINESS SCORING:
- 0.75+: High. Full prescribed volume and intensity. Good day to push top sets.
- 0.50-0.74: Moderate. Reduce intensity 5-10% or drop 1 set per exercise. Still train.
- Below 0.50: Low. Technique focus, 60-70% 1RM, cut volume in half. Consider active recovery day.

── INTRA-WORKOUT ADAPTATION ─────────────────────────────────────────────────

RIR-BASED SET ADJUSTMENTS:
- RIR 0 (hit failure): Overloaded. Drop 5-10% for compounds, 5-7.5% for isolation.
- RIR 1-2: Perfect working zone. Maintain weight. Pre-fill next set with same weight.
- RIR 3: Slightly light. Add small amount if early session (sets 1-2). Hold if late (3-4) — fatigue will close the gap.
- RIR 4+: Clearly underloaded. Add 5-10lbs compounds, 2.5-5lbs isolation. Max jump 10%.
- Never exceed a 10% jump between consecutive sets.
- Long lever athlete: extra conservative on shoulder/elbow dominant exercises — be conservative on RIR 3+ adjustments.

TOP SET + BACKOFF INTRA-WORKOUT:
- If top set RIR was 0 (failed), reduce backoffs by 10%.
- If top set RIR was 3+ (too easy), consider raising top set next session, not intra-session.
- Backoff sets should stay consistent — do not keep adding weight on backoffs.

CUMULATIVE FATIGUE:
- Set 4 is always harder than set 1 at the same weight. RIR decreases as session progresses.
- Do not interpret decreasing RIR as a signal to reduce weight mid-session — this is normal.
- Only adjust if RIR drops to 0 (failure) or was obviously miscalibrated from the first set.

=== END COACHING KNOWLEDGE BASE ===
"""

def get_user_id(authorization: Optional[str] = None) -> Optional[str]:
    """Extract user_id from Supabase JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        payload = pyjwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except Exception:
        return None

# ── DB Helpers ────────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def compute_banister(user_id=None):
    try:
        conn = get_conn()
        cur  = conn.cursor()
        if user_id:
            cur.execute("""
                SELECT date, exercise_name,
                       weight::float, reps::int
                FROM workouts
                WHERE weight IS NOT NULL AND reps IS NOT NULL
                  AND weight::float > 0 AND reps::int > 0
                  AND user_id = %s
                ORDER BY date
            """, (user_id,))
        else:
            cur.execute("""
                SELECT date, exercise_name,
                       weight::float, reps::int
                FROM workouts
                WHERE weight IS NOT NULL AND reps IS NOT NULL
                  AND weight::float > 0 AND reps::int > 0
                ORDER BY date
            """)
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f"DB error in compute_banister: {e}")
        raise RuntimeError(f"compute_banister query failed: {e}") from e

    if not rows:
        return 0, 0, []

    import pandas as pd
    df = pd.DataFrame(rows, columns=['date','exercise_name','weight','reps'])
    df['date'] = pd.to_datetime(df['date'])
    df['weight'] = pd.to_numeric(df['weight'], errors='coerce')
    df['reps']   = pd.to_numeric(df['reps'],   errors='coerce')
    df = df.dropna(subset=['weight', 'reps'])
    df = df[(df['weight'] > 0) & (df['reps'] > 0)]
    if df.empty:
        return 0, 0, []
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

def get_recent_performance(exercise_names, days=21):
    """
    Returns last 3 sessions per exercise with full pattern detection.
    Identifies: top_set_backoff, straight_sets, pyramid, reverse_pyramid, mixed.
    """
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cutoff = date.today() - timedelta(days=days)
        cur.execute("""
            SELECT exercise_name, date, set_order, weight, reps,
                   weight * (1 + reps / 30.0) as estimated_1rm
            FROM workouts
            WHERE weight > 0 AND reps > 0 AND date >= %s
            AND exercise_name = ANY(%s)
            ORDER BY exercise_name, date DESC, set_order ASC
        """, (cutoff, exercise_names))
        rows = cur.fetchall()
        conn.close()

        by_ex_date = defaultdict(lambda: defaultdict(list))
        for ex, d, s_order, w, r, e1rm in rows:
            by_ex_date[ex][str(d)].append({
                "set": s_order, "weight": float(w), "reps": float(r),
                "estimated_1rm": round(float(e1rm), 1)
            })

        result = {}
        for ex, dates in by_ex_date.items():
            result[ex] = []
            for d in sorted(dates.keys(), reverse=True)[:3]:
                sets = dates[d]
                weights = [s["weight"] for s in sets]

                top_set = max(sets, key=lambda s: s["estimated_1rm"])
                warmup_sets  = [s for s in sets if s["weight"] < top_set["weight"] * 0.85]
                backoff_sets = [s for s in sets if s["weight"] < top_set["weight"] * 0.97
                                and s["weight"] > top_set["weight"] * 0.75
                                and s != top_set and s["reps"] >= 3]

                if len(warmup_sets) >= 2 and len(backoff_sets) >= 1:
                    pattern = "top_set_backoff"
                elif len(set(round(w) for w in weights)) <= 2:
                    pattern = "straight_sets"
                elif weights == sorted(weights):
                    pattern = "pyramid"
                elif weights == sorted(weights, reverse=True):
                    pattern = "reverse_pyramid"
                else:
                    pattern = "mixed"

                working_candidates = [s for s in sets if s["reps"] >= 3 and s["weight"] >= top_set["weight"] * 0.80]
                working = max(working_candidates, key=lambda s: s["weight"]) if working_candidates else top_set

                backoff_summary = ""
                if backoff_sets:
                    avg_w = round(sum(s["weight"] for s in backoff_sets) / len(backoff_sets))
                    avg_r = round(sum(s["reps"]   for s in backoff_sets) / len(backoff_sets))
                    backoff_summary = f"{len(backoff_sets)}x{avg_r} @ {avg_w}lbs"

                result[ex].append({
                    "date":           d,
                    "pattern":        pattern,
                    "top_set":        f"{top_set['weight']}lbs x{int(top_set['reps'])}",
                    "working_weight": f"{working['weight']}lbs x{int(working['reps'])}",
                    "backoffs":       backoff_summary,
                    "total_sets":     len(sets),
                    "estimated_1rm":  top_set["estimated_1rm"]
                })
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

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Atlas API is running"}

@app.get("/debug/env")
def debug_env():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return {"has_key": bool(key), "key_prefix": key[:12] + "..." if len(key) > 12 else "EMPTY", "key_length": len(key)}

@app.get("/debug")
def debug():
    result = {"db_url_prefix": DATABASE_URL[:40]}
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM workouts")
        result["workout_rows_total"] = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM workouts
            WHERE weight IS NOT NULL AND reps IS NOT NULL
              AND weight::float > 0 AND reps::int > 0
        """)
        result["workout_rows_filterable"] = cur.fetchone()[0]
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'workouts' ORDER BY ordinal_position")
        result["workouts_schema"] = [{"col": r[0], "type": r[1]} for r in cur.fetchall()]
        conn.close()
        result["db_connected"] = True
    except Exception as e:
        result["db_connected"] = False
        result["error"] = str(e)
    try:
        fitness, fatigue, history = compute_banister()
        result["banister_fitness"]  = round(fitness, 1)
        result["banister_fatigue"]  = round(fatigue, 1)
        result["banister_history_days"] = len(history)
    except Exception as e:
        result["banister_error"] = str(e)
    return result

@app.get("/debug/exercise/{exercise_name}")
def debug_exercise(exercise_name: str, days: int = 30):
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cutoff = date.today() - timedelta(days=days)
        cur.execute("""
            SELECT date, workout_name, exercise_name, set_order, weight, reps
            FROM workouts WHERE exercise_name ILIKE %s AND date >= %s
            ORDER BY date DESC, set_order ASC
        """, (f"%{exercise_name}%", cutoff))
        rows = cur.fetchall()
        conn.close()
        return {"rows": [dict(r) for r in rows], "count": len(rows)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/state")
def get_state(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        fitness, fatigue, history = compute_banister(user_id)
        phase = detect_phase(fitness, fatigue)
        return {"fitness": round(fitness,1), "fatigue": round(fatigue,1),
                "performance": round(fitness-fatigue,1), "phase": phase, "history": history[-90:]}
    except Exception as e:
        print(f"Error in get_state: {e}")
        return {"fitness": 0, "fatigue": 0, "performance": 0, "phase": "accumulation", "history": [], "error": str(e)}

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
def get_today_checkin(authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if user_id:
            cur.execute("SELECT * FROM checkins WHERE date = %s AND user_id = %s", (date.today(), user_id))
        else:
            cur.execute("SELECT * FROM checkins WHERE date = %s", (date.today(),))
        row = cur.fetchone()
        conn.close()
        if not row: return {"exists": False}
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
def submit_checkin(payload: CheckInPayload, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    avg_soreness = sum(payload.soreness.values()) / max(len(payload.soreness), 1)
    readiness = round(
        0.35 * payload.sleep_quality + 0.30 * (1 - avg_soreness) +
        0.20 * payload.mood + 0.15 * (1 - payload.stress), 3
    )
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO checkins (
                user_id, date, sleep_hours, sleep_quality, mood, nutrition, stress,
                avg_soreness, readiness, notes,
                soreness_quads, soreness_hamstrings, soreness_glutes,
                soreness_back, soreness_chest, soreness_shoulders,
                soreness_biceps, soreness_triceps
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id, date) DO UPDATE SET
                sleep_hours=EXCLUDED.sleep_hours, sleep_quality=EXCLUDED.sleep_quality,
                mood=EXCLUDED.mood, nutrition=EXCLUDED.nutrition, stress=EXCLUDED.stress,
                avg_soreness=EXCLUDED.avg_soreness, readiness=EXCLUDED.readiness,
                notes=EXCLUDED.notes,
                soreness_quads=EXCLUDED.soreness_quads, soreness_hamstrings=EXCLUDED.soreness_hamstrings,
                soreness_glutes=EXCLUDED.soreness_glutes, soreness_back=EXCLUDED.soreness_back,
                soreness_chest=EXCLUDED.soreness_chest, soreness_shoulders=EXCLUDED.soreness_shoulders,
                soreness_biceps=EXCLUDED.soreness_biceps, soreness_triceps=EXCLUDED.soreness_triceps
        """, (
            user_id, date.today(), payload.sleep_hours, payload.sleep_quality,
            payload.mood, payload.nutrition, payload.stress,
            round(avg_soreness, 3), readiness, payload.notes,
            payload.soreness.get("quads",0), payload.soreness.get("hamstrings",0),
            payload.soreness.get("glutes",0), payload.soreness.get("back",0),
            payload.soreness.get("chest",0), payload.soreness.get("shoulders",0),
            payload.soreness.get("biceps",0), payload.soreness.get("triceps",0),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB error in submit_checkin: {e}")
    return {"readiness": readiness}

# ── AI Prescription ───────────────────────────────────────────────────────────
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
    phase    = detect_phase(fitness, fatigue)
    one_rms  = get_1rms()
    ex_names = [e["name"] for e in req.exercises]
    recent   = get_recent_performance(ex_names)

    soreness_summary = ", ".join(
        f"{m}: {'mild' if v <= 0.4 else 'high'}"
        for m, v in req.soreness.items() if v > 0
    ) or "none"

    exercise_lines = []
    for ex in req.exercises:
        name   = ex["name"]
        one_rm = one_rms.get(name, ex.get("oneRM"))
        note   = USER_PROFILE["exercise_notes"].get(name, "")
        recent_str = ""
        if name in recent:
            parts = []
            for s in recent[name]:
                part = f"[{s['date']} pattern={s['pattern']} top={s['top_set']}"
                if s['backoffs']:
                    part += f" backoffs={s['backoffs']}"
                part += f" e1rm~{s['estimated_1rm']}lbs]"
                parts.append(part)
            recent_str = " | sessions: " + "  ".join(parts)
        exercise_lines.append(
            f"- {name} (type={ex.get('type','compound')}, "
            f"est_1rm={str(one_rm)+'lbs' if one_rm else 'unknown'}"
            f"{recent_str}"
            f"{', note: '+note if note else ''})"
        )

    prompt = f"""{COACHING_KNOWLEDGE}

=== TODAY'S PRESCRIPTION REQUEST ===

ATHLETE: {USER_PROFILE['name']}
- {USER_PROFILE['height']}, {USER_PROFILE['weight']}, {USER_PROFILE['body_composition']}
- Level: {USER_PROFILE['training_level']} ({USER_PROFILE['training_years']} years)
- Current block: {USER_PROFILE['current_goal_block']}
- Active goals: {', '.join(USER_PROFILE['active_goals'])}
- All goals: {', '.join(USER_PROFILE['all_goals'])}
- Considerations: {'; '.join(USER_PROFILE['considerations'])}

TODAY'S STATUS:
- Readiness: {req.readiness:.2f}/1.0 ({'HIGH' if req.readiness >= 0.75 else 'MODERATE' if req.readiness >= 0.5 else 'LOW'})
- Sleep: {round(req.sleep*10)}/10, Mood: {round(req.mood*10)}/10, Nutrition: {round(req.nutrition*10)}/10, Stress: {round(req.stress*10)}/10
- Soreness: {soreness_summary}
- Banister phase: {phase.upper()} (fitness={round(fitness):,}, fatigue={round(fatigue):,})

EXERCISES TO PRESCRIBE:
{chr(10).join(exercise_lines)}

INSTRUCTIONS:
1. Identify the training pattern from recent session data (top_set_backoff, straight_sets, etc.)
2. Continue the athlete's established pattern — do not switch methods without reason.
3. For top_set_backoff: prescribe a top set (~2.5-5lbs above recent top set if it went well) and separate backoff sets at 88-92% of today's top set.
4. For straight_sets: small progressive jump over recent working weight.
5. NEVER prescribe multiple sets at a weight the athlete only hit as a near-max single.
6. Apply readiness-based adjustments from the knowledge base.
7. Pull-ups = bodyweight + added load. Skill work = progressions and hold times.
8. Give exact numbers — not ranges. Be specific.
9. Reference the athlete's actual recent numbers in coaching_note.

Respond ONLY with valid JSON, no other text:
{{
  "focus_cue": "One powerful coaching cue for today",
  "coaching_note": "2-3 sentences referencing actual recent numbers and training pattern. Be direct.",
  "exercises": [
    {{
      "name": "exercise name",
      "sets": 4,
      "reps": "5",
      "load": "215lbs",
      "intensity_note": "e.g. top set — 5lbs above last session / backoffs at 90% of top set",
      "cue": "one technique cue specific to this athlete"
    }}
  ],
  "recovery_note": "one sentence if relevant, else null"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 1200,
                      "messages": [{"role": "user", "content": prompt}]}
            )
        print(f"Anthropic status: {response.status_code}")
        print(f"Anthropic response: {response.text[:500]}")
        data = response.json()
        if "error" in data:
            return {"error": f"Anthropic error: {data['error'].get('message', str(data['error']))}"}
        text   = "".join(b.get("text", "") for b in data.get("content", []))
        clean  = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(clean)
        result["phase"] = phase
        return result
    except Exception as e:
        print(f"AI prescription error: {e}")
        return {"error": str(e)}

# ── Intra-workout Adaptation ──────────────────────────────────────────────────
class SetFeedback(BaseModel):
    exercise:          str
    prescribed_weight: float
    prescribed_reps:   int
    actual_weight:     float
    actual_reps:       int
    feeling:           str
    rir:               int = 2
    readiness:         float
    one_rm:            float = 0
    set_number:        int = 1
    total_sets:        int = 4
    exercise_type:     str = "compound"

@app.post("/adapt/set")
async def adapt_set(req: SetFeedback):
    if not ANTHROPIC_API_KEY:
        return {"error": "No API key configured"}

    prompt = f"""{COACHING_KNOWLEDGE}

=== INTRA-WORKOUT SET ADAPTATION ===

Athlete: {USER_PROFILE['name']}, {USER_PROFILE['height']}, {USER_PROFILE['weight']}, advanced lifter
Goals: {', '.join(USER_PROFILE['active_goals'])}
Considerations: {'; '.join(USER_PROFILE['considerations'])}

COMPLETED SET:
- Exercise: {req.exercise} ({req.exercise_type})
- Set {req.set_number} of {req.total_sets}
- Prescribed: {req.prescribed_weight}lbs x {req.prescribed_reps} reps
- Actual: {req.actual_weight}lbs x {req.actual_reps} reps
- RIR: {req.rir} {"— hit failure, too heavy" if req.rir == 0 else "— very easy, clearly too light" if req.rir >= 4 else ""}
- Estimated 1RM: {req.one_rm}lbs
- Readiness: {req.readiness}

Using the intra-workout RIR adjustment rules from the knowledge base, give one specific recommendation.
Account for: set position in session, long lever joint considerations, and cumulative fatigue.
Target RIR 1-2. Never suggest failure. One sentence, one specific weight.

Respond ONLY with JSON: {{"next_set": "one sentence with specific weight", "next_weight": 215, "next_reps": 5}}"""

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 150,
                      "messages": [{"role": "user", "content": prompt}]}
            )
        data  = response.json()
        if "error" in data:
            return {"error": data["error"].get("message", str(data["error"]))}
        text  = "".join(b.get("text", "") for b in data.get("content", []))
        clean = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e)}

# ── Formula Prescription (fallback) ──────────────────────────────────────────
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

    one_rms             = get_1rms()
    fitness, fatigue, _ = compute_banister()
    phase               = detect_phase(fitness, fatigue)
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
        sets = phase_config["sets"] if ex_type == "compound" else 3
        reps = phase_config["reps"] if ex_type == "compound" else (12 if ex_type == "isolation" else "max")
        sore_muscles = [m for m in ex_info.get("muscles_primary", []) if req.soreness.get(m, 0) >= 0.6]
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
            "exercise": ex_name, "sets": sets, "reps": reps, "weight": weight,
            "intensity_pct": pct, "estimated_1rm": round(one_rm, 1) if one_rm else None,
            "sore_warning": ", ".join(sore_muscles) if sore_muscles else None, "type": ex_type
        })

    return {"phase": phase, "prescriptions": results}

# ── History ───────────────────────────────────────────────────────────────────
# ── Workout Logging ───────────────────────────────────────────────────────────
class WorkoutSet(BaseModel):
    exercise_name: str
    set_order:     int
    weight:        float
    reps:          int
    rir:           int = None

class WorkoutLogRequest(BaseModel):
    workout_name: str
    sets:         list[WorkoutSet]

@app.post("/workout/log")
def log_workout(payload: WorkoutLogRequest, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        conn = get_conn()
        cur  = conn.cursor()
        today_date = date.today()
        # Delete existing sets for today + workout to allow re-logging
        if user_id:
            cur.execute("""
                DELETE FROM workouts
                WHERE user_id = %s AND date = %s AND workout_name = %s
            """, (user_id, today_date, payload.workout_name))
        for s in payload.sets:
            cur.execute("""
                INSERT INTO workouts (user_id, date, workout_name, exercise_name, set_order, weight, reps)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, today_date, payload.workout_name, s.exercise_name, s.set_order, s.weight, s.reps))
        conn.commit()
        conn.close()
        return {"ok": True, "sets_logged": len(payload.sets)}
    except Exception as e:
        print(f"DB error in log_workout: {e}")
        return {"ok": False, "error": str(e)}

# ── History ───────────────────────────────────────────────────────────────────
@app.get("/history/sessions")
def get_sessions(limit: int = 20, offset: int = 0, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if user_id:
            cur.execute("""
                SELECT date, workout_name,
                    COUNT(DISTINCT exercise_name) as exercise_count,
                    COUNT(*) as total_sets,
                    SUM(weight * reps) as total_volume
                FROM workouts WHERE user_id = %s
                GROUP BY date, workout_name
                ORDER BY date DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
        else:
            cur.execute("""
                SELECT date, workout_name,
                    COUNT(DISTINCT exercise_name) as exercise_count,
                    COUNT(*) as total_sets,
                    SUM(weight * reps) as total_volume
                FROM workouts
                GROUP BY date, workout_name
                ORDER BY date DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
        rows = cur.fetchall()
        if user_id:
            cur.execute("SELECT COUNT(DISTINCT date) as total FROM workouts WHERE user_id = %s", (user_id,))
        else:
            cur.execute("SELECT COUNT(DISTINCT date) as total FROM workouts")
        total = cur.fetchone()["total"]
        conn.close()
        return {"sessions": [dict(r) for r in rows], "total": total}
    except Exception as e:
        print(f"DB error in get_sessions: {e}")
        return {"sessions": [], "total": 0}

@app.get("/history/session/{session_date}")
def get_session_detail(session_date: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if user_id:
            cur.execute("""
                SELECT exercise_name, set_order, weight, reps,
                       weight * (1 + reps / 30.0) as estimated_1rm
                FROM workouts
                WHERE date = %s AND user_id = %s AND weight > 0 AND reps > 0
                ORDER BY exercise_name, set_order
            """, (session_date, user_id))
        else:
            cur.execute("""
                SELECT exercise_name, set_order, weight, reps,
                       weight * (1 + reps / 30.0) as estimated_1rm
                FROM workouts
                WHERE date = %s AND weight > 0 AND reps > 0
                ORDER BY exercise_name, set_order
            """, (session_date,))
        rows = cur.fetchall()
        conn.close()
        exercises = {}
        for r in rows:
            name = r["exercise_name"]
            if name not in exercises:
                exercises[name] = []
            exercises[name].append(dict(r))
        return {"date": session_date, "exercises": exercises}
    except Exception as e:
        print(f"DB error in get_session_detail: {e}")
        return {"date": session_date, "exercises": {}}

@app.get("/history/exercise/{exercise_name}")
def get_exercise_history(exercise_name: str, days: int = 365, authorization: Optional[str] = Header(None)):
    user_id = get_user_id(authorization)
    try:
        conn = get_conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cutoff = date.today() - timedelta(days=days)
        if user_id:
            cur.execute("""
                SELECT date,
                    MAX(weight * (1 + reps / 30.0)) as estimated_1rm,
                    MAX(weight) as max_weight,
                    (array_agg(reps ORDER BY (weight * (1 + reps/30.0)) DESC))[1] as max_reps
                FROM workouts
                WHERE exercise_name = %s AND user_id = %s AND weight > 0 AND reps > 0 AND date >= %s
                GROUP BY date ORDER BY date ASC
            """, (exercise_name, user_id, cutoff))
        else:
            cur.execute("""
                SELECT date,
                    MAX(weight * (1 + reps / 30.0)) as estimated_1rm,
                    MAX(weight) as max_weight,
                    (array_agg(reps ORDER BY (weight * (1 + reps/30.0)) DESC))[1] as max_reps
                FROM workouts
                WHERE exercise_name = %s AND weight > 0 AND reps > 0 AND date >= %s
                GROUP BY date ORDER BY date ASC
            """, (exercise_name, cutoff))
        rows = cur.fetchall()
        conn.close()
        return {"exercise": exercise_name, "history": [dict(r) for r in rows]}
    except Exception as e:
        print(f"DB error in get_exercise_history: {e}")
        return {"exercise": exercise_name, "history": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)