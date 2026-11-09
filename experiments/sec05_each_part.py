"""Section 5 - P alone, then add I, then add D. Theory vs simulation."""

import math
from common import plt, save, save_json, metrics_row, r, M, C, K, SETPOINT, DT
from pidlab import PID, mass_spring_damper, simulate, step_metrics


def second_order_prediction(kp, kd=0.0):
    """Closed loop with P or PD on m x'' + c x' + k x = u:
         m x'' + (c + Kd) x' + (k + Kp) x = Kp r
    """
    wn = math.sqrt((K + kp) / M)
    zeta = (C + kd) / (2 * math.sqrt(M * (K + kp)))
    final = kp / (K + kp)
    os_ = 100 * math.exp(-math.pi * zeta / math.sqrt(1 - zeta ** 2)) if zeta < 1 else 0.0
    return dict(wn=wn, zeta=zeta, final=final, sse=1 - final, overshoot=os_)


def two_panel(title):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    a1.axhline(SETPOINT, color="k", ls="--", lw=1, label="target")
    a1.set(xlabel="time [s]", ylabel="position [m]", title=title)
    a2.set(xlabel="time [s]", ylabel="force u [N]", title="Force the controller asks for")
    return fig, a1, a2


def main():
    plant = mass_spring_damper(M, C, K)
    results = {}

    # ---------------- P only ----------------
    fig, a1, a2 = two_panel("P only: bigger Kp = faster, but never reaches 1 m")
    rows = []
    for kp in (10, 50, 100, 300, 500):
        log = simulate(plant, PID(kp, 0, 0, dt=DT), SETPOINT, 2.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        p = second_order_prediction(kp)
        a1.plot(log["t"], log["y"], label=f"Kp={kp}")
        a2.plot(log["t"], log["u"], label=f"Kp={kp}")
        rows.append({"kp": kp, "pred_final_m": r(p["final"], 4), "sim_final_m": r(m["final"], 4),
                     "pred_sse_mm": r(p["sse"] * 1000, 1), "sim_sse_mm": r(m["sse"] * 1000, 1),
                     "zeta": r(p["zeta"]), "pred_os_pct": r(p["overshoot"], 1),
                     "sim_os_pct": r(m["overshoot"], 1), **{k: v for k, v in metrics_row(m).items()}})
    a1.set(xlim=(0, 1.2), ylim=(0, 1.55))
    a2.set(xlim=(0, 0.3), ylim=(-60, 520))
    a1.legend(ncol=2, loc="upper right")
    a2.legend(loc="upper right")
    save(fig, "fig05a_p_only.png")
    results["P"] = rows

    # ---------------- add I ----------------
    fig, a1, a2 = two_panel("PI (Kp = 30): I removes the offset; too much I overshoots")
    rows = []
    for ki in (0, 30, 70, 150):
        log = simulate(plant, PID(30, ki, 0, dt=DT), SETPOINT, 6.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        a1.plot(log["t"], log["y"], label=f"Ki={ki}")
        a2.plot(log["t"], log["u"], label=f"Ki={ki}")
        rows.append({"kp": 30, "ki": ki, **metrics_row(m)})
    a1.set(xlim=(0, 4), ylim=(0, 1.4))
    a2.set(xlim=(0, 4), ylim=(0, 40))
    a2.axhline(20, color="gray", ls=":", lw=1)
    a2.text(2.6, 21, "20 N = force to hold 1 m", fontsize=7.5, color="gray")
    a1.legend(ncol=2, loc="lower right")
    a2.legend(loc="upper right")
    save(fig, "fig05b_pi.png")
    results["PI"] = rows

    # ---------------- add D ----------------
    fig, a1, a2 = two_panel("PD (Kp = 300): more Kd = more damping, less bouncing")
    rows = []
    for kd in (0, 5, 10, 20, 40):
        log = simulate(plant, PID(300, 0, kd, dt=DT), SETPOINT, 2.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        p = second_order_prediction(300, kd)
        a1.plot(log["t"], log["y"], label=f"Kd={kd}")
        a2.plot(log["t"], log["u"], label=f"Kd={kd}")
        rows.append({"kp": 300, "kd": kd, "zeta": r(p["zeta"]), "pred_os_pct": r(p["overshoot"], 1),
                     "sim_os_pct": r(m["overshoot"], 1), **metrics_row(m)})
    a1.set(xlim=(0, 1.0), ylim=(0, 1.55))
    a2.set(xlim=(0, 0.4), ylim=(-150, 350))
    a1.legend(ncol=2, loc="upper right")
    a2.legend(loc="upper right")
    save(fig, "fig05c_pd.png")
    results["PD"] = rows
    save_json(results, "sec05.json")


if __name__ == "__main__":
    main()
