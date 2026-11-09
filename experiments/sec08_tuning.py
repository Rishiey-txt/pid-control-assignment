"""Section 8 - Ziegler-Nichols (ultimate-gain method) on G(s) = 1/(s+1)^3."""

import numpy as np
from common import plt, save, save_json, metrics_row, r
from pidlab import PID, third_order_lag, simulate, step_metrics

DT8 = 0.001
T_TEST = 40.0


def peaks(t, y):
    i = np.nonzero((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
    return t[i], y[i]


def growth_ratio(plant, kp):
    """Amplitude of a late swing divided by an early swing (1 = steady swinging)."""
    log = simulate(plant, PID(kp, dt=DT8), 1.0, T_TEST)
    tp, yp = peaks(log["t"], log["y"])
    y_mid = kp / (1 + kp)                 # the level P-only oscillates around
    a = yp - y_mid
    return a[-2] / a[1], log, tp


def find_ultimate_gain(plant):
    """'Raise P until it swings steadily' - automated with bisection."""
    lo, hi = 1.0, 20.0
    for _ in range(25):
        mid = 0.5 * (lo + hi)
        g, _, _ = growth_ratio(plant, mid)
        lo, hi = (mid, hi) if g < 1 else (lo, mid)
    ku = 0.5 * (lo + hi)
    _, log, tp = growth_ratio(plant, ku)
    pu = float(np.mean(np.diff(tp[1:])))
    return ku, pu, log


def main():
    plant = third_order_lag()
    ku, pu, _ = find_ultimate_gain(plant)
    print(f"  Ku = {ku:.3f} (theory 8), Pu = {pu:.3f} s (theory {2 * np.pi / np.sqrt(3):.3f} s)")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    for f, col in ((0.8, "tab:blue"), (1.0, "tab:green"), (1.1, "tab:red")):
        log = simulate(plant, PID(f * ku, dt=DT8), 1.0, 30.0)
        a1.plot(log["t"], log["y"], color=col, lw=1.2, label=f"Kp = {f * ku:.2f}" + ("  (= Ku)" if f == 1 else ""))
    tp, _ = peaks(*[simulate(plant, PID(ku, dt=DT8), 1.0, 30.0)[k] for k in ("t", "y")])
    a1.annotate("", xy=(tp[3], 1.95), xytext=(tp[2], 1.95), arrowprops=dict(arrowstyle="<->"))
    a1.text((tp[2] + tp[3]) / 2, 2.02, f"Pu = {pu:.2f} s", ha="center", fontsize=8)
    a1.set(xlim=(0, 30), ylim=(-0.4, 2.3), xlabel="time [s]", ylabel="output y [-]",
           title="Step 1: raise Kp until it swings steadily")
    a1.legend(loc="lower right", fontsize=7)

    rules = [
        ("Z-N classic PID", 0.6 * ku, pu / 2, pu / 8, "tab:red"),
        ("Z-N 'some overshoot'", ku / 3, pu / 2, pu / 3, "tab:orange"),
        ("Z-N 'no overshoot'", 0.2 * ku, pu / 2, pu / 3, "tab:purple"),
        ("hand-refined (ours)", 0.5 * ku, 1.5 * pu, pu / 4, "tab:blue"),
    ]
    rows = []
    a2.axhline(1, color="k", ls="--", lw=1)
    for name, kp, ti, td, col in rules:
        g = dict(kp=kp, ki=kp / ti, kd=kp * td)
        log = simulate(plant, PID(**g, dt=DT8), 1.0, T_TEST)
        m = step_metrics(log["t"], log["y"], 1.0)
        a2.plot(log["t"], log["y"], color=col, label=name)
        rows.append({"rule": name, "kp": r(g["kp"]), "ki": r(g["ki"]), "kd": r(g["kd"]),
                     "Ti_s": r(ti), "Td_s": r(td), **metrics_row(m)})
    a2.set(xlim=(0, 20), ylim=(0, 1.7), xlabel="time [s]", ylabel="output y [-]",
           title="Step 2: apply the recipe, then improve")
    a2.legend(loc="lower right", fontsize=7)
    save(fig, "fig08_zn.png")
    save_json({"Ku": r(ku), "Pu_s": r(pu), "Ku_theory": 8.0, "Pu_theory_s": r(2 * np.pi / np.sqrt(3)),
               "rules": rows}, "sec08.json")


if __name__ == "__main__":
    main()
