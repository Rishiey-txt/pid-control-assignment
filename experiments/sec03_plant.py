"""Section 3 - the test system without any controller (open loop)."""

import numpy as np
from common import plt, save, save_json, M, C, K, r
from pidlab import mass_spring_damper


def main():
    plant = mass_spring_damper(M, C, K)
    h, T = 1e-3, 3.0
    t = np.arange(0, T + h / 2, h)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for F, col in ((10, "tab:blue"), (20, "tab:green"), (30, "tab:orange")):
        plant.reset()
        x, v = [], []
        for _ in t:
            x.append(plant.x[0]); v.append(plant.x[1])
            plant.step(F, h)
        a1.plot(t, x, color=col, label=f"constant force {F} N  →  {F / K:.2f} m")
        if F == 20:
            x20, v20 = np.array(x), np.array(v)
    a1.axhline(1.0, ls="--", color="gray", lw=1, label="target 1 m")
    a1.set(xlabel="time [s]", ylabel="position x [m]", ylim=(0, 1.6),
           title="Open loop: force held constant, no feedback")
    a1.legend(loc="upper left")

    a2.plot(t, K * x20, color="tab:purple", label="spring force k·x")
    a2.plot(t, C * v20, color="tab:brown", label="damper force c·v")
    a2.plot(t, 20 - K * x20 - C * v20, color="tab:gray", label="left for acceleration m·a")
    a2.axhline(20, ls="--", color="tab:green", lw=1, label="applied force 20 N")
    a2.set(xlabel="time [s]", ylabel="force [N]", ylim=(-2, 22),
           title="Where the 20 N goes (F = 20 N case)")
    a2.legend(loc="center right")
    save(fig, "fig03_open_loop.png")

    poles = np.roots([M, C, K])
    zeta = C / (2 * np.sqrt(K * M))
    save_json({"poles": [r(p) for p in poles.real], "wn": r(np.sqrt(K / M)),
               "zeta": r(zeta), "dc_gain_m_per_N": r(1 / K, 4),
               "force_to_hold_1m_N": K * 1.0}, "sec03.json")


if __name__ == "__main__":
    main()
