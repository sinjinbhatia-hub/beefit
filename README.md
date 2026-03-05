# Atlas
### Adaptive Training & Load Optimization System

Atlas is a daily adaptive coaching system that replaces static weekly training programs with a data-driven, physiologically-grounded model that adjusts every single day based on who you are *that day*.

---

## The Problem

Every existing coaching model — human or app — operates on a fixed-schedule paradigm. A coach writes a program on Monday, you follow it all week regardless of what happens to your body, sleep, stress, or life. That's not optimization, that's scheduling.

A coach who sees you once a week has 1 data point. Atlas has 7, plus context a human coach never captures: how loud your dorm was, whether you had two exams, whether you ate once or three times.

**More data points = better optimization.**

---

## What Makes Atlas Different

- **No static schedules** — peak week, deload, and PR attempts are triggered by your actual fitness/fatigue curve, not a calendar
- **Multi-sport** — works for powerlifters, basketball players, golfers, calisthenics athletes, and anyone in between
- **Daily adaptation** — sleep 4 hours in a loud dorm? Your prescribed load drops automatically
- **Gets smarter over time** — model parameters are personalized to your physiology as data accumulates

---

## Mathematical Foundation

Built on the Banister Fitness-Fatigue Model (a system of first-order ODEs), with a daily readiness scoring layer, constrained load prescription, and a Bayesian updating mechanism for personalizing model parameters over time.

See `/design/math_model.md` for full derivation.

---

## Project Structure

```
atlas/
├── design/
│   ├── overview.md          # Vision, problem statement, product thesis
│   ├── math_model.md        # Full mathematical framework
│   └── data_structures.md  # Database schema and entity relationships
├── notebooks/
│   └── banister_model.ipynb # Math prototyping in Python
├── src/                     # Application code (coming soon)
└── README.md
```

---

## Status

> Currently in design phase. Mathematical framework complete. Data structures designed. Beginning Python prototype.

---

*Built by Sinjin Bhatia — Ohio State University, Mechanical Engineering & Applied Mathematics*
