"""Section 7 - four real-world problems, each shown and then fixed.

  (a) actuator limit 30 N  -> integral windup        fix: anti-windup
  (b) sensor noise +/-1 mm -> jumpy D term           fix: low-pass filter on D
  (c) sudden setpoint jump -> derivative kick        fix: D on measurement
  (d) slow controller      -> overshoot, instability fix: sample fast enough
"""

import numpy as np
from common import (plt, save, save_json, metrics_row, r, M, C, K, SETPOINT, DT, FINAL,
                    D_FILTER_TAU, U_MAX, NOISE)
from pidlab import PID, mass_spring_damper, simulate, step_metrics, step_setpoint


def windup(plant):
    cases = [
        ("no force limit (ideal)", dict(), "tab:gray"),
        ("30 N limit, no anti-windup", dict(u_min=-U_MAX, u_max=U_MAX, anti_windup=None), "tab:red"),
        ("30 N limit + clamping", dict(u_min=-U_MAX, u_max=U_MAX, anti_windup="clamp"), "tab:green"),
        ("30 N limit + back-calculation", dict(u_min=-U_MAX, u_max=U_MAX, anti_windup="backcalc"), "tab:blue"),
    ]
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(7.4, 2.6))
    rows = []
    for name, kw, col in cases:
        log = simulate(plant, PID(**FINAL, dt=DT, **kw), SETPOINT, 8.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        a1.plot(log["t"], log["y"], color=col, label=name)
        a2.plot(log["t"], log["u"], color=col, label=name)
        a3.plot(log["t"], log["i"], color=col, label=name)
        rows.append({"case": name, "max_I_term_N": r(max(log["i"]), 1), **metrics_row(m)})
    a1.axhline(SETPOINT, color="k", ls="--", lw=1)
    a1.set(xlim=(0, 3), ylim=(0, 1.45), xlabel="time [s]", ylabel="position [m]", title="Position")
    a2.set(xlim=(0, 3), ylim=(-35, 60), xlabel="time [s]", ylabel="force u [N]", title="Force sent to motor")
    a3.set(xlim=(0, 3), ylim=(0, 65), xlabel="time [s]", ylabel="I term [N]", title="Integral term")
    a3.axhline(20, color="gray", ls=":", lw=1)
    h, l = a1.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, fontsize=7, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle("(a) Windup: motor limited to ±30 N", y=1.0, fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, "fig07a_windup.png")
    return rows


def noise(plant):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    rows = []
    for name, tau, col in (("raw derivative", 0.0, "tab:red"),
                           (f"filtered derivative (τ = {D_FILTER_TAU * 1000:.0f} ms)", D_FILTER_TAU, "tab:blue")):
        log = simulate(plant, PID(**FINAL, dt=DT, d_filter_tau=tau), SETPOINT, 2.0, noise_amp=NOISE)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        sel = log["t"] >= 1.0
        a1.plot(log["t"], log["u"], color=col, lw=0.8, label=name)
        a2.plot(log["t"], (log["y"] - SETPOINT) * 1000, color=col, lw=1.0, label=f"true position, {name.split(' (')[0]}")
        rows.append({"case": name, "u_std_N": r(np.std(log["u"][sel]), 2),
                     "u_p2p_N": r(np.ptp(log["u"][sel]), 1),
                     "d_std_N": r(np.std(log["d"][sel]), 2),
                     "y_std_mm": r(np.std(log["y"][sel]) * 1000, 3), **metrics_row(m)})
        if tau == 0:
            a2.plot(log["t"], (log["y_meas"] - SETPOINT) * 1000, color="gray", lw=0.4, alpha=0.6,
                    label="what the sensor reports")
    a1.set(xlim=(1.0, 1.3), ylim=(-30, 70), xlabel="time [s]", ylabel="force u [N]",
           title="(b) Noise: force after settling (zoom)")
    a1.legend(loc="upper right")
    a2.set(xlim=(1.0, 1.3), ylim=(-1.6, 2.2), xlabel="time [s]", ylabel="position − target [mm]",
           title="Position error (zoom)")
    a2.legend(loc="upper right", fontsize=7)
    save(fig, "fig07b_noise.png")
    return rows


def kick(plant):
    sp = step_setpoint(SETPOINT, t_step=0.5)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    rows = []
    for name, dom, col in (("D on error (textbook)", False, "tab:red"),
                           ("D on measurement", True, "tab:blue")):
        log = simulate(plant, PID(**FINAL, dt=DT, d_on_measurement=dom), sp, 4.0)
        m = step_metrics(log["t"], log["y"], SETPOINT, t0=0.5)
        a1.plot(log["t"], log["u"], color=col, label=name)
        a2.plot(log["t"], log["y"], color=col, label=name)
        rows.append({"case": name, "peak_force_N": r(max(log["u"]), 0),
                     "peak_D_N": r(max(log["d"]), 0), **metrics_row(m)})
    a1.set_yscale("symlog", linthresh=100)
    a1.set(xlim=(0.4, 1.0), xlabel="time [s]", ylabel="force u [N] (log scale)",
           title="(c) Kick: target jumps 0 → 1 m at t = 0.5 s")
    a1.annotate(f"spike ≈ Kd·Δe/Δt\n= 20·1/0.001 = 20 000 N", xy=(0.5, 2e4), xytext=(0.6, 3e3),
                fontsize=8, arrowprops=dict(arrowstyle="->"))
    a1.legend(loc="lower right")
    a2.axhline(SETPOINT, color="k", ls="--", lw=1)
    a2.set(xlim=(0.4, 1.2), ylim=(-0.05, 1.3), xlabel="time [s]", ylabel="position [m]",
           title="Position")
    a2.legend(loc="lower right")
    save(fig, "fig07c_kick.png")
    return rows


def discrete_spectral_radius(plant, Ts, kp, ki, kd):
    """Exact stability test of the sampled loop (PID code + ZOH plant), r = 0.
    State z = [x (plant), I, y_prev]. Stable if every eigenvalue has |λ| < 1."""
    Ad, Bd = plant._discretise(Ts)
    Cm = plant.C[0]
    n = len(Cm)
    # u = -(kp + ki*Ts + kd/Ts) C x + I + (kd/Ts) y_prev
    Ku = np.concatenate([-(kp + ki * Ts + kd / Ts) * Cm, [1.0, kd / Ts]])
    Phi = np.zeros((n + 2, n + 2))
    Phi[:n, :n] = Ad
    Phi[:n] += np.outer(Bd, Ku)
    Phi[n, :n] = -ki * Ts * Cm
    Phi[n, n] = 1.0
    Phi[n + 1, :n] = Cm
    return float(max(abs(np.linalg.eigvals(Phi))))


def phase_margin(kp, ki, kd):
    w = np.logspace(-1, 3, 200000)
    s = 1j * w
    L = (kp + ki / s + kd * s) / (M * s ** 2 + C * s + K)
    i = int(np.argmin(abs(abs(L) - 1)))
    pm = 180 + np.degrees(np.angle(L[i]))
    return float(w[i]), float(pm)


def slow_update(plant):
    rows = []
    for Ts in (0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08):
        log = simulate(plant, PID(**FINAL, dt=Ts), SETPOINT, 10.0)
        m = step_metrics(log["t"], log["y"], SETPOINT)
        rows.append({"Ts_ms": round(Ts * 1000), "spectral_radius": r(discrete_spectral_radius(plant, Ts, **FINAL), 4),
                     "max_abs_y_m": r(max(abs(log["y"])), 3), **metrics_row(m)})
    # finest search for the stability limit
    Ts_grid = np.arange(0.040, 0.100, 0.0005)
    rho = [discrete_spectral_radius(plant, T, **FINAL) for T in Ts_grid]
    Ts_limit = float(Ts_grid[int(np.argmax(np.array(rho) >= 1.0))])
    wc, pm = phase_margin(**FINAL)
    # a ZOH behaves roughly like a delay of Ts/2; the backward-difference D adds about
    # another Ts/2 of lag on the dominant D term -> phase lost ~ wc*Ts (rad)
    Ts_pred = np.radians(pm) / wc

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for Ts, col in ((0.001, "tab:gray"), (0.04, "tab:blue"), (0.06, "tab:orange"), (0.08, "tab:red")):
        log = simulate(plant, PID(**FINAL, dt=Ts), SETPOINT, 2.0)
        a1.plot(log["t"], log["y"], color=col, label=f"update every {Ts * 1000:.0f} ms")
        a2.step(log["t"], log["u"], where="post", color=col, lw=1.0, label=f"{Ts * 1000:.0f} ms")
    a1.axhline(SETPOINT, color="k", ls="--", lw=1)
    a1.set(xlim=(0, 1.5), ylim=(-0.2, 2.0), xlabel="time [s]", ylabel="position [m]",
           title="(d) Slow controller updates")
    a1.legend(loc="upper right", fontsize=7)
    a2.set(xlim=(0, 1.0), ylim=(-150, 350), xlabel="time [s]", ylabel="force u [N]",
           title="Force is held between updates")
    a2.legend(loc="upper right", fontsize=7)
    save(fig, "fig07d_slow.png")
    return {"table": rows, "Ts_limit_exact_ms": round(Ts_limit * 1000, 1),
            "crossover_rad_s": r(wc, 2), "phase_margin_deg": r(pm, 1),
            "Ts_limit_rule_of_thumb_ms": round(Ts_pred * 1000, 1)}


def main():
    plant = mass_spring_damper(M, C, K)
    save_json({"windup": windup(plant), "noise": noise(plant), "kick": kick(plant),
               "slow": slow_update(plant)}, "sec07.json")


if __name__ == "__main__":
    main()
