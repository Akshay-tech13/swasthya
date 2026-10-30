#  Swasthya Symbol: worker health early-warning dashboard

An explainable, privacy-preserving early-warning dashboard for worker health.
It joins 3 simulated signals per site per week (clinic visits, sickness absence, environment heat/dust)
and warns when risk is rising, before it becomes a big problem.
It flags GROUPS (sites), never individuals. All data is SIMULATED and aggregated.

## How to run
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:AI_API_KEY="your-key"      # optional: without a key a fixed summary template is used
streamlit run app.py
```

## How it works
- `data/generator.py`: simulated data (seed 42), with known events (S1 outbreak, S5 heat, S7 data gap, S2 false spike).
- `core/detect.py`: EWMA (lambda 0.25) per signal against its first-12-weeks baseline, fused into a 0-100 risk score.
  Levels: Normal < 40, Watch 40-69, High >= 70. High needs 2 strong signals (alert-fatigue rule).
- `core/explain.py`, `core/actions.py`: "why this alert" and the recommended action with the responsible role.
- `core/quality.py`: data completeness badge. Missing signals are dropped and weights are renormalised.
- `core/backtest.py`: 10 simulated scenarios -> lead time, sensitivity, PPV, false alarms.
- `ai/`: plain-language summary in English or Hindi (Claude Sonnet). If the AI call fails, a fixed template is used.
- `api.py`: the only file the frontend imports from.

## Privacy
- Aggregated data only. Counts below 5 are hidden.
- Views depend on role: health officer (all), inspector (no clinic values), public (district level, environment only).
- Not for individual employment or disciplinary use. No worker records of any kind.

## Team
Frontend, Backend A (data, privacy, AI), Backend B + Integrator (detection, api, GitHub).

## Screenshots
<img width="1902" height="732" alt="image" src="https://github.com/user-attachments/assets/955da626-162d-4cac-a28d-6910e0417105" />
<img width="1907" height="837" alt="image" src="https://github.com/user-attachments/assets/0140fec4-e5eb-40f2-ad6b-3d8d1cf29229" />
<img width="1917" height="842" alt="image" src="https://github.com/user-attachments/assets/28f3d2fa-e8e1-4822-bda1-3323332e75bd" />
<img width="1917" height="827" alt="image" src="https://github.com/user-attachments/assets/65f96b27-1ed1-4404-bb71-8adcf4069cab" />




