"""Section 4 - the four performance measures, marked on one response."""

from common import plt, save, save_json, metrics_row, M, C, K, SETPOINT, DT
from pidlab import PID, mass_spring_damper, simulate, step_metrics


def main():
    plant = mass_spring_damper(M, C, K)
    log = simulate(plant, PID(300, 0, 0, dt=DT), SETPOINT, 2.0)
    t, y = log["t"], log["y"]
    m = step_metrics(t, y, SETPOINT)
    yf = m["final"]

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    ax.plot(t, y, color="tab:blue", label="position y(t), P-only Kp = 300")
    ax.axhline(SETPOINT, color="k", ls="--", lw=1, label="target 1 m")
    ax.axhline(yf, color="tab:gray", ls=":", lw=1.2, label=f"final value {yf:.4f} m")
    ax.fill_between(t, yf * 0.98, yf * 1.02, color="tab:green", alpha=0.15, label="±2 % settling band")

    # 1) rise time
    ax.plot([m["t10"], m["t90"]], [0.1 * yf, 0.9 * yf], "o", color="tab:orange")
    ax.annotate("", xy=(m["t90"], 0.5 * yf), xytext=(m["t10"], 0.5 * yf),
                arrowprops=dict(arrowstyle="<->", color="tab:orange"))
    ax.text(m["t90"] + 0.02, 0.45 * yf, f"① rise time (10→90 %)\n    = {m['rise']:.3f} s",
            color="tab:orange", fontsize=8.5)
    # 2) overshoot
    ax.annotate("", xy=(m["t_peak"], m["peak"]), xytext=(m["t_peak"], yf),
                arrowprops=dict(arrowstyle="<->", color="tab:red"))
    ax.text(m["t_peak"] + 0.03, m["peak"] - 0.06,
            f"② overshoot = {m['overshoot']:.1f} %\n    (peak {m['peak']:.3f} m)", color="tab:red", fontsize=8.5)
    # 3) settling time
    ax.axvline(m["settling"], color="tab:green", ls="--", lw=1)
    ax.text(m["settling"] + 0.02, 0.6, f"③ settling time (±2 %)\n    = {m['settling']:.3f} s",
            color="tab:green", fontsize=8.5)
    # 4) steady-state error
    ax.annotate("", xy=(1.85, SETPOINT), xytext=(1.85, yf),
                arrowprops=dict(arrowstyle="<->", color="tab:purple"))
    ax.text(1.38, 1.07, f"④ steady-state error\n    = {m['sse'] * 1000:.1f} mm",
            color="tab:purple", fontsize=8.5)

    ax.set(xlabel="time [s]", ylabel="position [m]", xlim=(0, 2), ylim=(0, 1.45),
           title="The four measures on one step response (target 0 → 1 m)")
    ax.legend(loc="lower right", ncol=2)
    save(fig, "fig04_metrics.png")
    save_json(metrics_row(m), "sec04.json")


if __name__ == "__main__":
    main()
