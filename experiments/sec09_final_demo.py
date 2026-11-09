"""Section 9 - the reusable PID with every Section-7 fix switched on, running
the test system through a realistic scenario:

  t = 0 s    target 0 -> 1 m
  t = 2 s    someone pushes the block with -5 N for good (a disturbance)
  t = 3.5 s  target 1 -> 0.5 m
with a 30 N motor, +/-1 mm sensor noise and a 1 kHz controller.
"""

from common import (plt, save, save_json, metrics_row, r, M, C, K, DT, FINAL,
                    D_FILTER_TAU, U_MAX, NOISE)
from pidlab import PID, mass_spring_damper, simulate, step_metrics


def setpoint(t):
    return 1.0 if t < 3.5 else 0.5


def disturbance(t):
    return -5.0 if t >= 2.0 else 0.0


def main():
    plant = mass_spring_damper(M, C, K)
    pid = PID(**FINAL, dt=DT, u_min=-U_MAX, u_max=U_MAX, anti_windup="backcalc",
              d_filter_tau=D_FILTER_TAU, d_on_measurement=True)
    log = simulate(plant, pid, setpoint, 5.5, noise_amp=NOISE, disturbance=disturbance, seed=1)
    t = log["t"]

    m1 = step_metrics(t[t < 2.0], log["y"][t < 2.0], 1.0)
    m2 = step_metrics(t[t >= 3.5], log["y"][t >= 3.5], 0.5, t0=3.5)
    after_push = (t >= 2.0) & (t < 3.5)
    dip = float(1.0 - min(log["y"][after_push]))
    recovered = t[after_push][(abs(log["y"][after_push] - 1.0) > 0.02 * 1.0)]
    recover_time = float(recovered[-1] - 2.0) if len(recovered) else 0.0

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 4.2), sharex=True)
    a1.plot(t, log["r"], "k--", lw=1, label="target")
    a1.plot(t, log["y_meas"], color="gray", lw=0.4, alpha=0.7, label="sensor reading (±1 mm noise)")
    a1.plot(t, log["y"], color="tab:blue", label="true position")
    a1.axvspan(2.0, 5.5, color="tab:red", alpha=0.05)
    a1.text(2.05, 0.3, "−5 N push from t = 2 s", color="tab:red", fontsize=8)
    a1.set(ylabel="position [m]", ylim=(0, 1.2),
           title="Final controller: 30 N limit, anti-windup, filtered D on measurement, noisy sensor")
    a1.legend(loc="lower right", ncol=3)
    a2.plot(t, log["u"], color="k", lw=0.9, label="force u (limited to ±30 N)")
    a2.plot(t, log["i"], color="tab:green", label="I term")
    a2.plot(t, log["p"], color="tab:blue", lw=0.8, alpha=0.7, label="P term")
    a2.axhline(U_MAX, color="tab:red", ls=":", lw=1)
    a2.axhline(-U_MAX, color="tab:red", ls=":", lw=1)
    a2.set(xlabel="time [s]", ylabel="force [N]", ylim=(-45, 45), xlim=(0, 5.5))
    a2.legend(loc="lower left", ncol=3)
    save(fig, "fig09_final_demo.png")

    save_json({"step_up": metrics_row(m1), "step_down": metrics_row(m2),
               "push_dip_mm": r(dip * 1000, 1), "push_recover_s": r(recover_time),
               "I_term_before_push_N": r(log["i"][(t > 1.8) & (t < 2.0)].mean(), 2),
               "I_term_after_push_N": r(log["i"][(t > 3.3) & (t < 3.5)].mean(), 2)}, "sec09.json")


if __name__ == "__main__":
    main()
