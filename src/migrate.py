import psycopg2
import psycopg2.extras
import pandas as pd
import json
import os
import io

DATABASE_URL = "postgresql://postgres:GUlVZnKeNQoLXPbOkIqyFAEcnCMHDVSF@shuttle.proxy.rlwy.net:31411/railway"

TRAINING_FILE  = "strong_workouts.csv"
CHECKIN_FILE   = "checkins.csv"
EXERCISES_FILE = "exercises.json"

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def create_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        DROP TABLE IF EXISTS workouts;
        DROP TABLE IF EXISTS checkins;
        DROP TABLE IF EXISTS exercises;

        CREATE TABLE workouts (
            id SERIAL PRIMARY KEY,
            date DATE,
            workout_name TEXT,
            exercise_name TEXT,
            set_order INTEGER,
            weight FLOAT,
            reps FLOAT,
            rpe FLOAT,
            notes TEXT
        );

        CREATE TABLE checkins (
            id SERIAL PRIMARY KEY,
            date DATE UNIQUE,
            sleep_hours FLOAT,
            sleep_quality FLOAT,
            mood FLOAT,
            nutrition FLOAT,
            stress FLOAT,
            avg_soreness FLOAT,
            readiness FLOAT,
            notes TEXT,
            soreness_quads FLOAT DEFAULT 0,
            soreness_hamstrings FLOAT DEFAULT 0,
            soreness_glutes FLOAT DEFAULT 0,
            soreness_back FLOAT DEFAULT 0,
            soreness_chest FLOAT DEFAULT 0,
            soreness_shoulders FLOAT DEFAULT 0,
            soreness_biceps FLOAT DEFAULT 0,
            soreness_triceps FLOAT DEFAULT 0
        );

        CREATE TABLE exercises (
            name TEXT PRIMARY KEY,
            muscles_primary TEXT[],
            muscles_secondary TEXT[],
            type TEXT,
            training_goal TEXT,
            equipment TEXT,
            one_rm_method TEXT
        );
    """)
    conn.commit()
    print("Tables created.")

def load_workouts(conn):
    df = pd.read_csv(TRAINING_FILE)
    df['Date']      = pd.to_datetime(df['Date']).dt.date
    df['Weight']    = pd.to_numeric(df['Weight'],    errors='coerce').fillna(0)
    df['Reps']      = pd.to_numeric(df['Reps'],      errors='coerce').fillna(0)
    df['Set Order'] = pd.to_numeric(df['Set Order'], errors='coerce').fillna(0).astype(int)
    df['RPE']       = pd.to_numeric(df['RPE'],       errors='coerce').fillna(0)

    out = pd.DataFrame({
        'date':          df['Date'],
        'workout_name':  df['Workout Name'].fillna('').astype(str),
        'exercise_name': df['Exercise Name'].fillna('').astype(str),
        'set_order':     df['Set Order'],
        'weight':        df['Weight'],
        'reps':          df['Reps'],
        'rpe':           df['RPE'],
        'notes':         ''
    })

    buf = io.StringIO()
    out.to_csv(buf, sep='\t', header=False, index=False)
    buf.seek(0)

    cur = conn.cursor()
    cur.copy_from(buf, 'workouts',
                  columns=('date','workout_name','exercise_name',
                            'set_order','weight','reps','rpe','notes'))
    conn.commit()
    print(f"Loaded {len(out)} workout rows.")

def load_checkins(conn):
    if not os.path.exists(CHECKIN_FILE):
        print("No checkins.csv found, skipping.")
        return

    df = pd.read_csv(CHECKIN_FILE)
    df['date'] = pd.to_datetime(df['date']).dt.date

    rows = [
        (
            row['date'],
            float(row.get('sleep_hours',   0)),
            float(row.get('sleep_quality', 0)),
            float(row.get('mood',          0)),
            float(row.get('nutrition',     0)),
            float(row.get('stress',        0)),
            float(row.get('avg_soreness',  0)),
            float(row.get('readiness',     0)),
            str(row.get('notes', '')),
            float(row.get('soreness_quads',      0)),
            float(row.get('soreness_hamstrings', 0)),
            float(row.get('soreness_glutes',     0)),
            float(row.get('soreness_back',       0)),
            float(row.get('soreness_chest',      0)),
            float(row.get('soreness_shoulders',  0)),
            float(row.get('soreness_biceps',     0)),
            float(row.get('soreness_triceps',    0)),
        )
        for _, row in df.iterrows()
    ]

    cur = conn.cursor()
    psycopg2.extras.execute_values(cur, """
        INSERT INTO checkins (
            date, sleep_hours, sleep_quality, mood, nutrition, stress,
            avg_soreness, readiness, notes,
            soreness_quads, soreness_hamstrings, soreness_glutes,
            soreness_back, soreness_chest, soreness_shoulders,
            soreness_biceps, soreness_triceps
        ) VALUES %s
        ON CONFLICT (date) DO UPDATE SET
            readiness = EXCLUDED.readiness,
            notes     = EXCLUDED.notes
    """, rows)
    conn.commit()
    print(f"Loaded {len(rows)} checkin rows.")

def load_exercises(conn):
    with open(EXERCISES_FILE, 'r') as f:
        data = json.load(f)

    rows = [
        (
            name,
            ex.get('muscles_primary',   []),
            ex.get('muscles_secondary', []),
            ex.get('type',          ''),
            ex.get('training_goal', ''),
            ex.get('equipment',     ''),
            ex.get('1rm_method',    '')
        )
        for name, ex in data['exercises'].items()
    ]

    cur = conn.cursor()
    psycopg2.extras.execute_values(cur, """
        INSERT INTO exercises (name, muscles_primary, muscles_secondary,
                               type, training_goal, equipment, one_rm_method)
        VALUES %s
    """, rows)
    conn.commit()
    print(f"Loaded {len(rows)} exercises.")

if __name__ == "__main__":
    print("Connecting to database...")
    conn = get_conn()
    print("Connected.")
    create_tables(conn)
    load_workouts(conn)
    load_checkins(conn)
    load_exercises(conn)
    conn.close()
    print("Migration complete.")
