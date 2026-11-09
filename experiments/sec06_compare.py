"""Section 6 - P vs PI vs PD vs PID, and how the final gains were chosen."""

from common import plt, save, save_json, metrics_row, M, C, K, SETPOINT, DT, FINAL
from pidlab import PID, mass_spring_damper, simulate, step_metrics

CANDIDATES = [
    ("P   (Kp=300)", dict(kp=300)),
    ("PI  (Kp=30, Ki=70)", dict(kp=30, ki=70)),
    ("PD  (Kp=300, Kd=20)", dict(kp=300, kd=20)),
    ("PID (Kp=300, Ki=200, Kd=20)", FINAL),
]


def main():
    plant = mass_spring_damper(M, C, K)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.8))
    a1.axhline(SETPOINT, color="k", ls="--", lw=1, label="target")
    table = []
    for name, g in CANDIDATES:
        log = simulate(plant, PID(**g, dt=DT), SETPOINT, 5.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        a1.plot(log["t"], log["y"], label=name)
        a2.plot(log["t"], log["u"], label=name)
        table.append({"name": name.split()[0], "gains": name.split(None, 1)[1].strip("()"),
                      "peak_force_N": round(float(max(log["u"])), 1), **metrics_row(m)})
    a1.set(xlim=(0, 1.5), ylim=(0, 1.5), xlabel="time [s]", ylabel="position [m]",
           title="P, PI, PD and PID on the same step")
    a1.legend(loc="upper right", fontsize=7)
    a2.set(xlim=(0, 0.5), ylim=(-50, 320), xlabel="time [s]", ylabel="force u [N]",
           title="Force used")
    a2.legend(loc="upper right", fontsize=7)
    save(fig, "fig06_compare.png")

    # how much Ki to add on top of the PD design (Kp=300, Kd=20)
    ki_sweep = []
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    ax.axhline(SETPOINT, color="k", ls="--", lw=1, label="target")
    for ki in (0, 100, 200, 400, 800):
        log = simulate(plant, PID(300, ki, 20, dt=DT), SETPOINT, 5.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        ax.plot(log["t"], log["y"], label=f"Ki={ki}", lw=2.2 if ki == 200 else 1.3)
        ki_sweep.append({"ki": ki, **metrics_row(m)})
    ax.set(xlim=(0, 1.5), ylim=(0.6, 1.2), xlabel="time [s]", ylabel="position [m]",
           title="Choosing Ki with Kp = 300, Kd = 20 fixed (zoomed near the target)")
    ax.legend(ncol=3, loc="lower right")
    save(fig, "fig06b_ki_choice.png")
    save_json({"compare": table, "ki_sweep": ki_sweep}, "sec06.json")


if __name__ == "__main__":
    main()
