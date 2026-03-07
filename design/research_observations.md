## 2026-03-04
Model peaks in mid-2023 despite similar or higher strength levels now.
Hypothesis 1: Volume was higher in 2023 (more sets/exercises)
Hypothesis 2: Form improvements reduced working weight temporarily, 
              lowering TRIMP despite real strength gains
Hypothesis 3: TRIMP doesn't account for technique quality as a load modifier
Question: Can we add a technique confidence multiplier to the TRIMP formula?

Core Product Philosophy — March 4 2026
The app should feel like a coach who knows everything about exercise science AND knows you personally. It presents evidence for why something is prescribed, but listens when you push back. It works around your preferences because enjoyment and consistency beat the perfect program every time. A 70% optimal program you stick to for 2 years beats a 100% optimal program you quit in 3 weeks.
Two types of users:

Has a routine — knows what they do, wants it optimized daily
Needs a program — tell us your goal, your preferences, what you enjoy, what you hate, and we build something evidence-based around you

Both types get daily adaptation. Both types get coached, not just scheduled

# 2026-03-06

Atlas — Product Observations & Roadmap Notes

---

## Bugs (Quick Fixes)

### 1. "New Day" button doesn't reset date
- Clicking "New Day" reloads the page but the date display doesn't change
- Root cause: `window.location.reload()` is fine, but the date is computed at render time — this might be a timezone or caching issue
- Fix: Replace reload with proper state reset, force fresh date computation

---

## Features In Progress

### 2. Prescription quality — needs to be science-based
Current state: Prescription is a rough intensity formula (75% 1RM, fixed sets/reps). Not actionable.

What it should be:
- **Sport-specific periodization**: powerlifting, bodybuilding, athletic training have different rep ranges, rest periods, progression schemes
- **Progressive overload logic**: track week-over-week progression per exercise, not just today's 1RM estimate
- **Phase-appropriate prescription**:
  - Accumulation: 4×8-12 @ 65-75%, shorter rest, higher volume
  - Intensification: 4-5×4-6 @ 80-87%, longer rest, moderate volume
  - Peak: 3-5×1-3 @ 88-95%, full rest, low volume
  - Deload: 3×10-15 @ 50-60%, minimal fatigue
- **AI-assisted prescription**: use Claude API to generate intelligent, contextual prescription based on readiness + recent load + muscle soreness + phase

### 3. Readiness-aware split suggestion
Current state: User picks split manually, soreness adjusts weight slightly.

What it should be:
- If readiness is low AND target muscles are sore → suggest postponing, show preview of tomorrow's adjusted plan
- "Your legs are sore and readiness is 0.51. Consider hitting Upper Push today and saving Lower for tomorrow when recovery is better."
- Show a "suggested" split badge based on: soreness map + last trained date per muscle group + current phase
- AI layer: Claude reads the full context and generates a natural language recommendation

---

## Planned Features

### 4. Workout log / history
- Need a full log of completed workouts (like Strong app's history)
- Each session: date, split, exercises, sets/reps/weight, notes
- Currently have 15,231 sets in the DB from Strong import — need a UI to browse them
- Filter by exercise, date range, muscle group
- Progress charts per exercise (e.g. bench press 1RM over time)

### 5. Check-in history
- Log of all past check-ins with readiness scores
- Trend line: readiness over time
- Correlate readiness with training load (TRIMP) — "you feel best 2 days after heavy lower"
- Eventually: pattern recognition via AI

### 6. AI-powered features (future)
Use Claude API embedded in the app for:
- Smart prescription generation with natural language explanation
- Recovery recommendations ("you've had 4 heavy sessions this week, consider a deload")
- Injury risk flags based on soreness patterns
- Goal-specific periodization plans (powerlifting meet prep, hypertrophy block, athletic season)
- Weekly summary: "Last week you hit 4 sessions, TRIMP was 18K, performance score is up 3%"

---

## Sport-Specific Training Science (to implement in prescription engine)

### Powerlifting / Strength
- Primary lifts: Squat, Bench, Deadlift + variations
- Rep ranges: 1-6, intensity 80-95%
- Periodization: linear or daily undulating (DUP)
- Key metric: 1RM progression, total volume at >85%

### Hypertrophy / Bodybuilding
- Rep ranges: 8-15, intensity 60-80%
- Volume: 10-20 sets per muscle group per week
- Key metric: weekly volume per muscle group, progressive overload

### Athletic / Sport Performance
- Mixed qualities: power, speed, strength-endurance
- Periodization: block periodization with distinct phases
- Key metric: power output, rate of force development

### Endurance / Conditioning
- Different TRIMP model needed (HR-based vs load-based)
- Taper logic before events

---

## UI / UX Notes

### Current issues
- Half-screen layout (max-width: 1100px) — intentional for desktop, needs responsive mobile layout
- "New Day" flow is clunky — should feel more like opening the app fresh each morning

### Mobile app vision
- React Native or PWA wrapper around the same API
- Morning routine flow: open app → check-in → get prescription → go train
- Push notifications: "Time to check in" morning reminder
- Offline mode: prescription cached locally if no connection at gym

---

## Priority Order (suggested)

1. Fix "New Day" date bug
2. Add workout history UI (browse past sessions, progress charts)
3. Improve prescription engine (science-based, phase-appropriate)
4. AI prescription layer (Claude API integration)
5. Readiness-aware split suggestion
6. Check-in history + readiness trends
7. Sport-specific profiles
8. Mobile app
# Atlas — Product Observations & Roadmap Notes
*Captured: March 6, 2026*

---

## Bugs (Quick Fixes)

### 1. "New Day" button doesn't reset date
- Clicking "New Day" reloads the page but the date display doesn't change
- Root cause: `window.location.reload()` is fine, but the date is computed at render time — this might be a timezone or caching issue
- Fix: Replace reload with proper state reset, force fresh date computation

---

## Features In Progress

### 2. Prescription quality — needs to be science-based
Current state: Prescription is a rough intensity formula (75% 1RM, fixed sets/reps). Not actionable.

What it should be:
- **Sport-specific periodization**: powerlifting, bodybuilding, athletic training have different rep ranges, rest periods, progression schemes
- **Progressive overload logic**: track week-over-week progression per exercise, not just today's 1RM estimate
- **Phase-appropriate prescription**:
  - Accumulation: 4×8-12 @ 65-75%, shorter rest, higher volume
  - Intensification: 4-5×4-6 @ 80-87%, longer rest, moderate volume
  - Peak: 3-5×1-3 @ 88-95%, full rest, low volume
  - Deload: 3×10-15 @ 50-60%, minimal fatigue
- **AI-assisted prescription**: use Claude API to generate intelligent, contextual prescription based on readiness + recent load + muscle soreness + phase

### 3. Readiness-aware split suggestion
Current state: User picks split manually, soreness adjusts weight slightly.

What it should be:
- If readiness is low AND target muscles are sore → suggest postponing, show preview of tomorrow's adjusted plan
- "Your legs are sore and readiness is 0.51. Consider hitting Upper Push today and saving Lower for tomorrow when recovery is better."
- Show a "suggested" split badge based on: soreness map + last trained date per muscle group + current phase
- AI layer: Claude reads the full context and generates a natural language recommendation

---

## Planned Features

### 4. Workout log / history
- Need a full log of completed workouts (like Strong app's history)
- Each session: date, split, exercises, sets/reps/weight, notes
- Currently have 15,231 sets in the DB from Strong import — need a UI to browse them
- Filter by exercise, date range, muscle group
- Progress charts per exercise (e.g. bench press 1RM over time)

### 5. Check-in history
- Log of all past check-ins with readiness scores
- Trend line: readiness over time
- Correlate readiness with training load (TRIMP) — "you feel best 2 days after heavy lower"
- Eventually: pattern recognition via AI

### 6. AI-powered features (future)
Use Claude API embedded in the app for:
- Smart prescription generation with natural language explanation
- Recovery recommendations ("you've had 4 heavy sessions this week, consider a deload")
- Injury risk flags based on soreness patterns
- Goal-specific periodization plans (powerlifting meet prep, hypertrophy block, athletic season)
- Weekly summary: "Last week you hit 4 sessions, TRIMP was 18K, performance score is up 3%"

---

## Sport-Specific Training Science (to implement in prescription engine)

### Powerlifting / Strength
- Primary lifts: Squat, Bench, Deadlift + variations
- Rep ranges: 1-6, intensity 80-95%
- Periodization: linear or daily undulating (DUP)
- Key metric: 1RM progression, total volume at >85%

### Hypertrophy / Bodybuilding
- Rep ranges: 8-15, intensity 60-80%
- Volume: 10-20 sets per muscle group per week
- Key metric: weekly volume per muscle group, progressive overload

### Athletic / Sport Performance
- Mixed qualities: power, speed, strength-endurance
- Periodization: block periodization with distinct phases
- Key metric: power output, rate of force development

### Endurance / Conditioning
- Different TRIMP model needed (HR-based vs load-based)
- Taper logic before events

---

## UI / UX Notes

### Current issues
- Half-screen layout (max-width: 1100px) — intentional for desktop, needs responsive mobile layout
- "New Day" flow is clunky — should feel more like opening the app fresh each morning

### Mobile app vision
- React Native or PWA wrapper around the same API
- Morning routine flow: open app → check-in → get prescription → go train
- Push notifications: "Time to check in" morning reminder
- Offline mode: prescription cached locally if no connection at gym

---

## Priority Order (suggested)

1. Fix "New Day" date bug
2. Add workout history UI (browse past sessions, progress charts)
3. Improve prescription engine (science-based, phase-appropriate)
4. AI prescription layer (Claude API integration)
5. Readiness-aware split suggestion
6. Check-in history + readiness trends
7. Sport-specific profiles
8. Mobile app


---

## User Profile — Sinjin

### Physical
- Height: 6'2", Weight: 185lbs, Body composition: lean/shredded
- Training level: Advanced (3-7 years)
- Age: [to add]

### Goals (prioritized, not simultaneous)
1. **Immediate**: Weighted pull-up +175lbs bodyweight, Bench 315
2. **Near-term**: Windmill dunk (vertical + athleticism)
3. **Long-term**: Full planche, Front lever (calisthenics strength)
4. **Strength milestone**: 405 squat

### Goal insight
Goals shift over time — not chasing all simultaneously. Current block = strength (pull, press). 
Future block = relative strength / skill (planche, front lever require different loading philosophy — 
lower absolute load, higher skill/tension work). AI needs to understand goal sequencing.

### AI Coach Philosophy
- Meet the user where they are, not where an average person is
- Push the user — don't coddle, but don't destroy
- Feedback loop: every session/week the user can rate how the prescription felt → AI adjusts
- Long-term planning: 5-year optimization calendar, adaptable when goals or life changes
- Not about hitting the goal every session — about structuring the journey intelligently

### Exercise-specific load profiles (critical)
- Pull-ups ≠ squats: bodyweight movements scale differently, RPE matters more than % 1RM
- Planche/front lever: skill-based, isometric holds, progressive leverage changes (not load)
- Dunking/athleticism: power/plyometric work, different periodization than strength
- Each exercise needs its own prescription logic, not a one-size formula

### Considerations AI must always factor
- Joint sensitivity (long levers at 6'2" = more torque on knees, shoulders, elbows)
- Previous injuries (to be logged)
- Recovery capacity (age-related, lifestyle)
- Sleep, stress, nutrition from daily check-in
- Feedback from last session

---

## AI Coach Architecture (to build)

### User profile stored in DB
```
users table:
  - age, height, weight, training_level
  - primary_goal, goal_timeline
  - injuries (JSON array)
  - joint_notes
  - sport_profile (strength/hypertrophy/athletic/skill)
```

### Goal sequencing engine
- Active goal block (e.g. "Strength Block — Pull + Press")
- Goal unlock logic: when pull-up +175 is hit → shift focus
- 5-year calendar: rough macro periodization with goal milestones
- AI recalibrates when user logs a goal hit or reports a life change

### Session feedback loop
- After each prescription: user rates difficulty (too easy / right / too hard)
- After each session: log actual sets/reps/weight vs prescribed
- AI reads delta → adjusts next session

### Prompt structure for Claude API
Each prescription call sends:
- User profile (age, height, goals, injuries)
- Current phase + readiness score
- Soreness map
- Selected exercises
- Recent performance (last 3 sessions per exercise)
- Last session feedback rating
- Active goal block

Claude returns:
- Sets/reps/weight per exercise with rationale
- Today's focus cue (1 sentence)
- Recovery note if readiness is low
- Goal progress note ("You're 3 sessions from hitting your pull-up target weight")


---

## New Features (March 6 session)

### 7. Mid-workout tracking (like Strong)
- Log actual sets/reps/weight as you do them during the session
- Rest timers between sets (configurable per exercise type)
- Simple logging UI: tap to complete a set, enter actual weight/reps
- Compare actual vs prescribed in real time

### 8. Intra-workout AI adaptation
- After completing a set, user rates it: Easy / On Point / Too Hard
- AI immediately suggests adjustment for next set:
  - Easy → "Stay at weight or add 5-10lbs"
  - Too Hard → "Drop to Xlbs for next set"
- End of session: AI compares prescribed vs actual and adjusts next session
- This is the core feedback loop that makes the prescription get smarter over time

### 9. AI fatigue calibration
- Even at high readiness, recommendations were slightly aggressive
- Adjust prompt to be more conservative by default — advanced lifters still need joint/tendon longevity
- Add a "conservative buffer" even at peak readiness (e.g. leave 1-2 reps in reserve)
- Readiness 0.8+ → push hard but not to absolute limit
- Readiness 0.6-0.8 → moderate, clear RIR guidance
- Readiness < 0.6 → significantly reduced, technique focus


---

## Production Roadmap — App Store Launch

### Architecture (already correct)
- API key lives on server only, never in the app
- Frontend talks to Railway backend, backend talks to Anthropic
- This scales cleanly to multi-user

### Pre-launch checklist

**1. User authentication**
- Sign up / login (email + password or OAuth with Google/Apple)
- JWT tokens for authenticated requests
- Library: FastAPI + python-jose for backend, Auth0 or Supabase for easy setup

**2. Multi-user database**
- Add `user_id` foreign key to all tables (workouts, checkins, exercises)
- Currently assumes one user — needs to be scoped per account
- Each user gets their own Banister model, check-in history, goals

**3. User profile in DB**
- Age, height, weight, training level
- Goals (with active block tracking)
- Injury history
- Sport profile
- Currently hardcoded in server.py as USER_PROFILE — needs to move to DB

**4. Subscriptions (Stripe)**
- $10-15/month per user
- API cost per user per day: ~$0.01-0.05 (very cheap)
- Stripe webhooks to activate/deactivate accounts
- Free tier option: limited prescriptions per week, no AI coach

**5. Mobile app**
- React Native wrapping the same API
- Or PWA (Progressive Web App) — simpler, can be added to home screen, App Store via wrapper
- Morning flow: open → check in → get prescription → go train
- Mid-workout tracker with rest timers

**6. Railway → Production infra**
- Fix env var injection or migrate to Render/Fly.io
- Add proper DATABASE_URL via connection pooling (PgBouncer)
- Set up staging vs production environments

**7. App Store submission**
- Apple Developer account ($99/year)
- Google Play account ($25 one-time)
- App Review: need privacy policy, terms of service
- Health & Fitness category

### Monetization model
- Free: basic tracking, no AI coach
- Pro ($12.99/month): AI prescriptions, full history, goal planning
- Annual ($99/year): ~35% discount

### Timeline estimate
- V1 (personal use, current): Done
- V2 (multi-user, auth, subscriptions): 4-6 weeks
- App Store submission: 6-8 weeks from now


---

## Monetization Model (Updated)

### Structure: Freemium + $25/year Premium

**Free tier (forever)**
- Workout logging and history
- Check-in and readiness score
- Basic prescription (formula-based, no AI)
- Banister fitness/fatigue tracking
- Goal setting and tracking

**Premium ($25/year)**
- AI coach prescriptions
- Intra-workout AI adaptation
- Readiness-aware split suggestions
- Long-term goal planning (5-year calendar)
- Advanced analytics and trends
- Priority support

### Economics
- API cost per AI prescription: ~$0.01-0.02
- User training 4x/week = ~200 sessions/year = ~$2-4 in API costs
- $25/year leaves ~$21-23 margin per user after API costs
- At 1,000 premium users: ~$21,000/year revenue
- At 10,000 premium users: ~$210,000/year revenue
- Price is low enough to be a no-brainer for serious athletes

### Why this works
- Free tier has real value — removes barrier to download and daily use
- $25/year is less than one month at most fitness apps
- No subscription anxiety — pay once a year and forget it
- AI is the clear upgrade driver — users will feel the difference immediately