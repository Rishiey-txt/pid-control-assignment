"""Quick 'what if' runs for the interview: change one thing, see the four measures.

Examples
    python whatif.py                          # final controller, ideal conditions
    python whatif.py --mass 2                 # heavier block
    python whatif.py --umax 30 --noise 0.001  # realistic motor + sensor
    python whatif.py --kp 500 --ki 0 --kd 0   # P only
    python whatif.py --umax 15                # motor weaker than the 20 N holding force
    python whatif.py --compare mass=1,2,4 --umax 30   # overlay several values on one plot
"""

import argparse
import os

import matplotlib
import numpy as np

from pidlab import PID, mass_spring_damper, simulate, step_metrics, fmt_metrics

PARAMS = ("kp", "ki", "kd", "mass", "damping", "spring", "umax", "noise", "dt", "tau", "setpoint")


def run(a):
    plant = mass_spring_damper(a.mass, a.damping, a.spring)
    lim = a.umax if a.umax > 0 else np.inf
    pid = PID(a.kp, a.ki, a.kd, dt=a.dt, u_min=-lim, u_max=lim,
              anti_windup=None if a.no_antiwindup else "backcalc",
              d_filter_tau=a.tau, d_on_measurement=not a.d_on_error)
    log = simulate(plant, pid, a.setpoint, a.time, noise_amp=a.noise)
    return log, step_metrics(log["t"], log["y"], a.setpoint)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kp", type=float, default=300)
    p.add_argument("--ki", type=float, default=200)
    p.add_argument("--kd", type=float, default=20)
    p.add_argument("--mass", type=float, default=1.0, help="kg")
    p.add_argument("--damping", type=float, default=10.0, help="N*s/m")
    p.add_argument("--spring", type=float, default=20.0, help="N/m")
    p.add_argument("--umax", type=float, default=0, help="force limit in N (0 = none)")
    p.add_argument("--noise", type=float, default=0, help="sensor noise amplitude in m (e.g. 0.001)")
    p.add_argument("--dt", type=float, default=0.001, help="controller sample time in s")
    p.add_argument("--tau", type=float, default=0.005, help="D filter time constant in s (0 = off)")
    p.add_argument("--setpoint", type=float, default=1.0, help="m")
    p.add_argument("--time", type=float, default=5.0, help="simulated seconds")
    p.add_argument("--no-antiwindup", action="store_true")
    p.add_argument("--d-on-error", action="store_true", help="textbook D (shows the kick)")
    p.add_argument("--compare", help="e.g. mass=1,2,4 or kp=100,300,500")
    p.add_argument("--plot", action="store_true", help="show a plot window")
    a = p.parse_args()

    runs = []
    if a.compare:
        name, vals = a.compare.split("=")
        assert name in PARAMS, f"--compare must be one of {PARAMS}"
        for v in vals.split(","):
            setattr(a, name, float(v))
            log, m = run(a)
            runs.append((f"{name}={v}", log, m))
    else:
        log, m = run(a)
        runs.append(("run", log, m))

    for label, log, m in runs:
        extra = f" | peak force {max(abs(log['u'])):.1f} N | final {m['final']:.4f} m"
        print(f"{label:>12}: {fmt_metrics(m)}{extra}")

    if a.plot or a.compare:
        if not a.plot:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2))
        for label, log, _ in runs:
            a1.plot(log["t"], log["y"], label=label)
            a2.plot(log["t"], log["u"], label=label)
        a1.axhline(a.setpoint, color="k", ls="--", lw=1)
        a1.set(xlabel="time [s]", ylabel="position [m]", title="What-if: position")
        a2.set(xlabel="time [s]", ylabel="force [N]", title="What-if: force")
        a1.legend(); a2.legend()
        fig.tight_layout()
        if a.plot:
            plt.show()
        else:
            os.makedirs("figures", exist_ok=True)
            fig.savefig("figures/whatif.png", dpi=150)
            print("saved figures/whatif.png")


if __name__ == "__main__":
    main()
