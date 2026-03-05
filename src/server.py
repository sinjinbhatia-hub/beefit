from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import json
import os
from datetime import date, timedelta

app = FastAPI()

# ── Allow React frontend to talk to this server ────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── File paths ─────────────────────────────────────────────────────
TRAINING_FILE  = "strong_workouts.csv"
CHECKIN_FILE   = "checkins.csv"
EXERCISES_FILE = "exercises.json"
USER           = "sinjin"
TAU_FITNESS    = 45
TAU_FATIGUE    = 7

# ── Shared helpers ─────────────────────────────────────────────────
def compute_banister():
    df = pd.read_csv(TRAINING_FILE)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df[df["Weight"] > 0].copy()
    df["estimated_1rm"] = df["Weight"] * (1 + df["Reps"] / 30)
    df = df.sort_values("Date")
    df["max_1rm"] = df.groupby("Exercise Name")["estimated_1rm"].cummax()
    df["intensity"] = df["Weight"] / df["max_1rm"]
    df["trimp_set"] = df["Weight"] * df["Reps"] * (df["intensity"] ** 2)
    daily = df.groupby("Date")["trimp_set"].sum().reset_index()
    daily.columns = ["date", "trimp"]
    daily["date"] = pd.to_datetime(daily["date"])
    all_dates = pd.date_range(daily["date"].min(), date.today())
    daily = daily.set_index("date").reindex(all_dates, fill_value=0).reset_index()
    daily.columns = ["date", "trimp"]
    fitness, fatigue = 0, 0
    history = []
    for _, row in daily.iterrows():
        fitness = fitness * np.exp(-1 / TAU_FITNESS) + row["trimp"]
        fatigue = fatigue * np.exp(-1 / TAU_FATIGUE) + row["trimp"]
        history.append({"date": str(row["date"].date()), "trimp": round(row["trimp"], 1),
                        "fitness": round(fitness, 1), "fatigue": round(fatigue, 1),
                        "performance": round(fitness - fatigue, 1)})
    return fitness, fatigue, history

def get_1rms():
    df = pd.read_csv(TRAINING_FILE)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df[df["Weight"] > 0].copy()
    df["estimated_1rm"] = df["Weight"] * (1 + df["Reps"] / 30)
    cutoff = date.today() - timedelta(days=90)
    df = df[df["Date"] >= cutoff]
    return df.groupby("Exercise Name")["estimated_1rm"].max().to_dict()

def detect_phase(fitness, fatigue):
    ratio = fatigue / fitness if fitness > 0 else 0
    if ratio > 1.3:    return "deload"
    elif ratio > 1.1:  return "peak"
    elif ratio > 0.85: return "intensification"
    else:              return "accumulation"

def compute_base_load():
    df = pd.read_csv(TRAINING_FILE)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df = df[df["Weight"] > 0].copy()
    df["estimated_1rm"] = df["Weight"] * (1 + df["Reps"] / 30)
    df = df.sort_values("Date")
    df["max_1rm"] = df.groupby("Exercise Name")["estimated_1rm"].cummax()
    df["intensity"] = df["Weight"] / df["max_1rm"]
    df["trimp_set"] = df["Weight"] * df["Reps"] * (df["intensity"] ** 2)
    daily = df.groupby("Date")["trimp_set"].sum().reset_index()
    daily.columns = ["date", "trimp"]
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    cutoff = date.today() - timedelta(days=7)
    recent = daily[daily["date"] >= cutoff]
    return float(recent["trimp"].mean()) if not recent.empty else 500.0

# ── Routes ─────────────────────────────────────────────────────────

@app.get("/state")
def get_state():
    """Returns current Banister state, phase, and last 90 days of history"""
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
    """Returns exercise database and user splits"""
    with open(EXERCISES_FILE, "r") as f:
        data = json.load(f)
    one_rms = get_1rms()
    # Inject current 1RM estimates into exercise list
    for name, ex in data["exercises"].items():
        ex["estimated_1rm"] = round(one_rms.get(name, 0), 1)
    return data

@app.get("/checkin/today")
def get_today_checkin():
    """Returns today's check-in if it exists"""
    if not os.path.exists(CHECKIN_FILE):
        return {"exists": False}
    df = pd.read_csv(CHECKIN_FILE)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    today_row = df[df["date"] == date.today()]
    if today_row.empty:
        return {"exists": False}
    row = today_row.iloc[-1].to_dict()
    return {"exists": True, "data": row}

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
    """Saves a check-in and returns computed readiness score"""
    avg_soreness = sum(payload.soreness.values()) / len(payload.soreness)
    readiness = round(
        0.35 * payload.sleep_quality +
        0.30 * (1 - avg_soreness) +
        0.20 * payload.mood +
        0.15 * (1 - payload.stress),
        3
    )
    row = {
        "date":           date.today().isoformat(),
        "sleep_hours":    payload.sleep_hours,
        "sleep_quality":  payload.sleep_quality,
        "mood":           payload.mood,
        "nutrition":      payload.nutrition,
        "stress":         payload.stress,
        "avg_soreness":   round(avg_soreness, 3),
        "readiness":      readiness,
        "notes":          payload.notes,
        **{f"soreness_{k}": v for k, v in payload.soreness.items()}
    }
    file_exists = os.path.exists(CHECKIN_FILE)
    pd.DataFrame([row]).to_csv(
        CHECKIN_FILE, mode="a",
        header=not file_exists,
        index=False
    )
    return {"readiness": readiness, "row": row}

class PrescriptionRequest(BaseModel):
    exercises:  list
    readiness:  float
    soreness:   dict

@app.post("/prescribe")
def prescribe(req: PrescriptionRequest):
    """Returns prescription for a list of exercises"""
    with open(EXERCISES_FILE, "r") as f:
        ex_data = json.load(f)

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
    results = []

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

        # Soreness check
        sore_muscles = [m for m in ex_info.get("muscles_primary", [])
                        if req.soreness.get(m, 0) >= 0.6]
        if sore_muscles:
            intensity = round(intensity * 0.85, 3)
            sets = max(2, sets - 1)

        one_rm = one_rms.get(ex_name)
        if ex_type in ["skill", "endurance"] or not one_rm:
            weight = None
            pct    = None
        else:
            weight = round((one_rm * intensity) / 2.5) * 2.5
            pct    = round(intensity * 100)

        results.append({
            "exercise":     ex_name,
            "sets":         sets,
            "reps":         reps,
            "weight":       weight,
            "intensity_pct": pct,
            "estimated_1rm": round(one_rm, 1) if one_rm else None,
            "sore_warning": ", ".join(sore_muscles) if sore_muscles else None,
            "type":         ex_type
        })

    return {"phase": phase, "prescriptions": results}

# ── Run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
