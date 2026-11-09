# PID Control: from zero to working code

Code for the Modern Monk Labs *Physical AI* intern assignment on PID control.
Everything is written from scratch in Python with **NumPy + Matplotlib only**. No control library is used: the
PID, the plant simulation (exact zero-order hold via a hand-written matrix exponential) and the
performance measures are all in `pidlab/`.

The report is in [`report/PID_Report.pdf`](report/PID_Report.pdf).

## Quick start

```bash
git clone https://github.com/Rishiey-txt/pid-control-assignment.git && cd pid-control-assignment
python3 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py          # recreates every graph in figures/ and every number in results/  (~5 s)
```

Every script is deterministic: the noise uses a fixed random seed, so everyone gets the same graphs.
You can also run a single section, e.g. `python experiments/sec07_real_world.py`.

## What each script produces

| Report section | Script | Figures | Numbers |
|---|---|---|---|
| 1 Basic idea (loop diagram) | `experiments/sec01_loop_diagram.py` | `fig01_loop.png` | – |
| 2 PID formula (what P/I/D see) | `experiments/sec02_pid_terms.py` | `fig02_pid_terms.png` | – |
| 3 Test system (open loop) | `experiments/sec03_plant.py` | `fig03_open_loop.png` | `sec03.json` |
| 4 Four measures | `experiments/sec04_metrics.py` | `fig04_metrics.png` | `sec04.json` |
| 5 P, then I, then D | `experiments/sec05_each_part.py` | `fig05a_p_only.png`, `fig05b_pi.png`, `fig05c_pd.png` | `sec05.json` (theory vs simulation) |
| 6 P / PI / PD / PID + choosing Ki | `experiments/sec06_compare.py` | `fig06_compare.png`, `fig06b_ki_choice.png` | `sec06.json` |
| 7 Windup, noise, kick, slow update | `experiments/sec07_real_world.py` | `fig07a_windup.png` … `fig07d_slow.png` | `sec07.json` (incl. exact stability limit) |
| 8 Ziegler–Nichols on 1/(s+1)³ | `experiments/sec08_tuning.py` | `fig08_zn.png` | `sec08.json` |
| 9 Final controller demo | `experiments/sec09_final_demo.py` | `fig09_final_demo.png` | `sec09.json` |

## Repository layout

```
pidlab/
  controller.py   PID class: output limits, anti-windup (clamp / back-calculation),
                  filtered derivative, derivative-on-measurement, explicit sample time
  plants.py       state-space plants + exact ZOH discretisation (NumPy matrix exponential)
                  mass_spring_damper(m=1, c=10, k=20), third_order_lag() = 1/(s+1)^3
  simulate.py     closed-loop simulation (controller every Ts, plant logged every 1 ms)
  metrics.py      rise time (10–90 %), overshoot, settling time (±2 %), steady-state error
experiments/      one script per report section (see table above)
run_all.py        runs all experiments
whatif.py         change one parameter and see what happens (interview helper)
report/           build_report.py → PID_Report.html → PID_Report.pdf
figures/, results/  generated output
```

## Using the controller

```python
from pidlab import PID, mass_spring_damper, simulate, step_metrics

pid = PID(kp=300, ki=200, kd=20, dt=0.001,          # final gains from Section 6
          u_min=-30, u_max=30,                       # 30 N motor
          anti_windup="backcalc",                    # fix (a)
          d_filter_tau=0.005,                        # fix (b)
          d_on_measurement=True)                     # fix (c)

# on hardware: call once every dt seconds
u = pid.update(setpoint, sensor_reading)

# in simulation
log = simulate(mass_spring_damper(), pid, setpoint=1.0, t_end=3.0, noise_amp=0.001)
print(step_metrics(log["t"], log["y"]))
```

## What-if experiments

```bash
python whatif.py                                   # final controller, ideal conditions
python whatif.py --mass 2                          # heavier block
python whatif.py --umax 30 --noise 0.001           # realistic motor and sensor
python whatif.py --compare mass=1,2,4 --umax 30    # overlay -> figures/whatif.png
python whatif.py --compare umax=15,20,30           # motor weaker than the 20 N holding force
python whatif.py --kp 300 --ki 0 --kd 0            # P only
python whatif.py --umax 30 --no-antiwindup         # see windup
python whatif.py --d-on-error --tau 0 --noise 0.001  # textbook D on a noisy sensor
```

## Rebuilding the PDF report

Requires Google Chrome (used headless to print HTML to PDF). Edit `AUTHOR` and `GITHUB` at the top
of `report/build_report.py`, then:

```bash
python run_all.py && python report/build_report.py
```

All numbers in the report text are read from `results/*.json`, so the PDF always matches the code.

## Use of AI tools

Claude (Anthropic) helped structure the code and draft the report text. All results come from
running this code and were checked against hand calculations (P-only steady-state error,
damping-ratio overshoot formula, exact discrete-time stability limit, and the analytic ultimate gain
K<sub>u</sub> = 8 / period 2π/√3 s for 1/(s+1)³).
