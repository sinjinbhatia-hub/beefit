## 2026-03-04
Model peaks in mid-2023 despite similar or higher strength levels now.
Hypothesis 1: Volume was higher in 2023 (more sets/exercises)
Hypothesis 2: Form improvements reduced working weight temporarily, 
              lowering TRIMP despite real strength gains
Hypothesis 3: TRIMP doesn't account for technique quality as a load modifier
Question: Can we add a technique confidence multiplier to the TRIMP formula?

<<<<<<< HEAD
Core Product Philosophy — March 4 2026
The app should feel like a coach who knows everything about exercise science AND knows you personally. It presents evidence for why something is prescribed, but listens when you push back. It works around your preferences because enjoyment and consistency beat the perfect program every time. A 70% optimal program you stick to for 2 years beats a 100% optimal program you quit in 3 weeks.
Two types of users:

Has a routine — knows what they do, wants it optimized daily
Needs a program — tell us your goal, your preferences, what you enjoy, what you hate, and we build something evidence-based around you

Both types get daily adaptation. Both types get coached, not just scheduled
=======
When using historical 1RM the model gives a semi-inaccurate prediction of what current maxes are. Because it doesn't account for changes in changing, weight, form. By using a rolling window of data instead it can give a better model.
    -used 90 day rolling window, and 1RMs are spot on.
>>>>>>> 6a44fca (Add exercise database, split selection, rep range logic, soreness adjustments)
