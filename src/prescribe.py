import pandas as pd
import numpy as np
import os
import json
from datetime import date, timedelta

# ── File paths ─────────────────────────────────────────────────────
CHECKIN_FILE   = 'checkins.csv'
TRAINING_FILE  = 'strong_workouts.csv'
EXERCISES_FILE = 'exercises.json'
USER           = 'sinjin'

# ── Banister parameters ────────────────────────────────────────────
TAU_FITNESS = 45
TAU_FATIGUE = 7

# ── Phase configs ──────────────────────────────────────────────────
PHASES = {
    'accumulation':    {'multiplier': 1.1,  'intensity': 0.75, 'sets': 4, 'reps': 8},
    'intensification': {'multiplier': 0.95, 'intensity': 0.85, 'sets': 4, 'reps': 5},
    'peak':            {'multiplier': 0.75, 'intensity': 0.92, 'sets': 3, 'reps': 3},
    'deload':          {'multiplier': 0.45, 'intensity': 0.55, 'sets': 3, 'reps': 10},
}

# ── Load exercise database ─────────────────────────────────────────
def load_exercises():
    with open(EXERCISES_FILE, 'r') as f:
        return json.load(f)

# ── Ask user what workout they're doing today ──────────────────────
def ask_workout(exercise_data):
    splits = exercise_data['splits'][USER]
    workout_names = list(splits.keys())

    print("\nWhat are you training today?")
    for i, name in enumerate(workout_names):
        print(f"  {i+1}. {name}")
    print(f"  {len(workout_names)+1}. Custom (enter your own exercises)")

    while True:
        try:
            choice = int(input("\nEnter number: "))
            if 1 <= choice <= len(workout_names):
                selected = workout_names[choice - 1]
                all_exercises = splits[selected]

                # Let user pick which exercises today
                print(f"\nExercises in {selected} — select today's (e.g. 1,3,5):")
                for i, ex in enumerate(all_exercises):
                    print(f"  {i+1}. {ex}")
                print(f"  or press Enter to use all")

                picks = input("\nYour selection: ").strip()
                if picks == '':
                    return selected, all_exercises
                else:
                    indices = [int(x.strip()) - 1 for x in picks.split(',')]
                    chosen = [all_exercises[i] for i in indices if 0 <= i < len(all_exercises)]
                    return selected, chosen

            elif choice == len(workout_names) + 1:
                custom = input("Enter exercises separated by commas: ")
                exercises = [e.strip() for e in custom.split(',')]
                return "Custom", exercises
        except ValueError:
            pass
        print("Invalid choice, try again.")

# ── Banister state ─────────────────────────────────────────────────
def compute_banister():
    df = pd.read_csv(TRAINING_FILE)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df[df['Weight'] > 0].copy()
    df['estimated_1rm'] = df['Weight'] * (1 + df['Reps'] / 30)
    df = df.sort_values('Date')
    df['max_1rm'] = df.groupby('Exercise Name')['estimated_1rm'].cummax()
    df['intensity'] = df['Weight'] / df['max_1rm']
    df['trimp_set'] = df['Weight'] * df['Reps'] * (df['intensity'] ** 2)
    daily = df.groupby('Date')['trimp_set'].sum().reset_index()
    daily.columns = ['date', 'trimp']
    daily['date'] = pd.to_datetime(daily['date'])
    daily = daily.sort_values('date')
    all_dates = pd.date_range(daily['date'].min(), date.today())
    daily = daily.set_index('date').reindex(all_dates, fill_value=0).reset_index()
    daily.columns = ['date', 'trimp']
    fitness, fatigue = 0, 0
    for _, row in daily.iterrows():
        fitness = fitness * np.exp(-1 / TAU_FITNESS) + row['trimp']
        fatigue = fatigue * np.exp(-1 / TAU_FATIGUE) + row['trimp']
    return fitness, fatigue

# ── Base load ──────────────────────────────────────────────────────
def compute_base_load():
    df = pd.read_csv(TRAINING_FILE)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df[df['Weight'] > 0].copy()
    df['estimated_1rm'] = df['Weight'] * (1 + df['Reps'] / 30)
    df = df.sort_values('Date')
    df['max_1rm'] = df.groupby('Exercise Name')['estimated_1rm'].cummax()
    df['intensity'] = df['Weight'] / df['max_1rm']
    df['trimp_set'] = df['Weight'] * df['Reps'] * (df['intensity'] ** 2)
    daily = df.groupby('Date')['trimp_set'].sum().reset_index()
    daily.columns = ['date', 'trimp']
    daily['date'] = pd.to_datetime(daily['date']).dt.date
    cutoff = date.today() - timedelta(days=7)
    recent = daily[daily['date'] >= cutoff]
    return recent['trimp'].mean() if not recent.empty else 500

# ── Recent 1RM estimates (90 day window) ───────────────────────────
def get_1rms():
    df = pd.read_csv(TRAINING_FILE)
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df[df['Weight'] > 0].copy()
    df['estimated_1rm'] = df['Weight'] * (1 + df['Reps'] / 30)
    cutoff = date.today() - timedelta(days=90)
    df = df[df['Date'] >= cutoff]
    return df.groupby('Exercise Name')['estimated_1rm'].max()

# ── Phase detection ────────────────────────────────────────────────
def detect_phase(fitness, fatigue):
    ratio = fatigue / fitness if fitness > 0 else 0
    if ratio > 1.3:    return 'deload'
    elif ratio > 1.1:  return 'peak'
    elif ratio > 0.85: return 'intensification'
    else:              return 'accumulation'

# ── Prescribe a single exercise ────────────────────────────────────
def prescribe_exercise(name, phase_config, one_rms, exercise_data, soreness_map):
    ex_info   = exercise_data['exercises'].get(name)
    intensity = phase_config['intensity']

    # ── Rep ranges by exercise type ────────────────────────────────
    if ex_info:
        if ex_info['type'] == 'compound':
            sets, reps = phase_config['sets'], phase_config['reps']
        elif ex_info['type'] == 'isolation':
            sets, reps = 3, 12  # isolation always higher reps
        elif ex_info['type'] == 'skill':
            sets, reps = 4, 'max'
        else:
            sets, reps = 3, 12
    else:
        sets, reps = phase_config['sets'], phase_config['reps']

    # ── Soreness check ─────────────────────────────────────────────
    sore_warning = None
    if ex_info:
        sore_muscles = [m for m in ex_info['muscles_primary']
                        if soreness_map.get(f'soreness_{m}', 0) >= 0.6]
        if sore_muscles:
            sore_warning = ', '.join(sore_muscles)
            intensity = round(intensity * 0.85, 2)  # reduce 15%
            sets = max(2, sets - 1)                 # drop a set

        # Skill/endurance — no weight prescription
        if ex_info.get('training_goal') in ['skill', 'endurance']:
            return {
                'exercise':     name,
                'sets':         sets,
                'reps':         'max',
                'weight':       'bodyweight',
                'note':         'focus on form and time under tension',
                'sore_warning': sore_warning
            }

    # ── Weight based exercises ─────────────────────────────────────
    if name not in one_rms.index:
        return {
            'exercise':     name,
            'sets':         sets,
            'reps':         reps,
            'weight':       'no data — start light and log this session',
            'sore_warning': sore_warning
        }

    one_rm = one_rms[name]
    weight = round((one_rm * intensity) / 2.5) * 2.5

    return {
        'exercise':     name,
        'sets':         sets,
        'reps':         reps,
        'weight':       weight,
        'intensity_pct': round(intensity * 100),
        'estimated_1rm': round(one_rm, 1),
        'sore_warning': sore_warning
    }

# ── Readiness ──────────────────────────────────────────────────────
def get_readiness():
    if not os.path.exists(CHECKIN_FILE):
        print("No check-in found. Run checkin.py first.")
        return None, None
    df = pd.read_csv(CHECKIN_FILE)
    df['date'] = pd.to_datetime(df['date']).dt.date
    today_row = df[df['date'] == date.today()]
    if today_row.empty:
        print("No check-in for today. Run checkin.py first.")
        return None, None
    row = today_row.iloc[-1]
    return float(row['readiness']), row

# ── Main ───────────────────────────────────────────────────────────
def run_prescription():
    print("\nBuilding your training state...")
    exercise_data      = load_exercises()
    fitness, fatigue   = compute_banister()
    performance        = fitness - fatigue
    base_load          = compute_base_load()
    readiness, checkin = get_readiness()

    if readiness is None:
        return

    phase        = detect_phase(fitness, fatigue)
    phase_config = PHASES[phase]
    one_rms      = get_1rms()

    # Build soreness map from check-in
    soreness_map = {col: float(checkin[col])
                    for col in checkin.index if col.startswith('soreness_')}

    # Ask what workout today
    workout_name, exercises = ask_workout(exercise_data)

    print(f"\n{'='*50}")
    print(f"  ATLAS — Training Prescription")
    print(f"  {date.today()}  |  {workout_name}")
    print(f"{'='*50}")
    print(f"  Fitness:     {fitness:.0f}")
    print(f"  Fatigue:     {fatigue:.0f}")
    print(f"  Performance: {performance:.0f}")
    print(f"  Readiness:   {readiness:.2f} / 1.0")
    print(f"  Phase:       {phase.upper()}")
    print(f"\n  TODAY'S PRESCRIPTION:")
    print(f"  {'─'*40}")

    for ex_name in exercises:
        p = prescribe_exercise(ex_name, phase_config, one_rms,
                               exercise_data, soreness_map)
        print(f"\n  {p['exercise']}")
        if p['weight'] == 'bodyweight':
            print(f"    {p['sets']} sets × {p['reps']} — {p['note']}")
        elif isinstance(p['weight'], str):
            print(f"    {p['sets']} sets × {p['reps']} reps — {p['weight']}")
        else:
            print(f"    {p['sets']} sets × {p['reps']} reps @ {p['weight']}lbs ({p['intensity_pct']}% of {p['estimated_1rm']}lb 1RM)")
        if p['sore_warning']:
            print(f"    ⚠ {p['sore_warning']} sore — load reduced 15%, set dropped")

    print(f"\n{'='*50}\n")

if __name__ == '__main__':
    run_prescription()