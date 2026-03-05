import pandas as pd
from datetime import date, timedelta
from collections import defaultdict
import json

# ── Load data ──────────────────────────────────────────────────────
df = pd.read_csv('strong_workouts.csv')
df['Date'] = pd.to_datetime(df['Date'])
df['date_only'] = df['Date'].dt.date

# ── Filter to last 6 weeks ─────────────────────────────────────────
cutoff = date.today() - timedelta(weeks=6)
df_recent = df[df['date_only'] >= cutoff].copy()

# ── Map exercises to workout names ─────────────────────────────────
split = defaultdict(set)
for _, row in df_recent.iterrows():
    split[row['Workout Name']].add(row['Exercise Name'])

# ── Get best recent weight per exercise ───────────────────────────
df_weights = df_recent[df_recent['Weight'] > 0].copy()
df_weights['estimated_1rm'] = df_weights['Weight'] * (1 + df_weights['Reps'] / 30)
best_weights = df_weights.groupby('Exercise Name').agg(
    max_weight=('Weight', 'max'),
    estimated_1rm=('estimated_1rm', 'max'),
    times_performed=('Exercise Name', 'count')
).reset_index().sort_values('times_performed', ascending=False)

# ── Print detected split by workout name ──────────────────────────
print("\n=== DETECTED SPLIT (by workout name) ===\n")
for workout_name, exercises in sorted(split.items()):
    print(f"{workout_name}:")
    for ex in sorted(exercises):
        print(f"  - {ex}")
    print()

# ── Print top exercises ────────────────────────────────────────────
print("\n=== TOP EXERCISES BY FREQUENCY ===\n")
print(best_weights.head(20).to_string(index=False))

# ── Save to JSON ───────────────────────────────────────────────────
split_clean = {name: sorted(list(exs)) for name, exs in split.items()}
output = {
    "detected_split": split_clean,
    "top_exercises": best_weights.head(20).to_dict(orient='records')
}
with open('detected_split.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\nDetected split saved to detected_split.json")
