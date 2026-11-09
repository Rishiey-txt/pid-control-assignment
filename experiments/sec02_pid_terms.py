"""Section 2 - what P, I and D each 'look at' during a real step response."""

import numpy as np
from common import plt, save, M, C, K, SETPOINT, DT, FINAL, D_FILTER_TAU
from pidlab import PID, mass_spring_damper, simulate


def main():
    plant = mass_spring_damper(M, C, K)
    pid = PID(**FINAL, dt=DT, d_filter_tau=D_FILTER_TAU)
    log = simulate(plant, pid, SETPOINT, 1.0)
    t, e = log["t"], log["r"] - log["y"]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7))
    a1.plot(t, e, color="k", label="error e(t) = r − y")
    a1.fill_between(t, 0, e, color="tab:green", alpha=0.25, label="area = ∫e dt  (I looks here)")
    k = int(0.06 / (t[1] - t[0]))
    slope = (e[k + 1] - e[k - 1]) / (t[k + 1] - t[k - 1])
    tt = np.array([0.0, 0.14])
    a1.plot(tt, e[k] + slope * (tt - t[k]), "--", color="tab:red", label="slope = de/dt  (D looks here)")
    a1.plot(t[k], e[k], "o", color="tab:blue", label="value now = e  (P looks here)")
    a1.set(xlim=(0, 0.6), ylim=(-0.05, 1.05), xlabel="time [s]", ylabel="error [m]",
           title="One error signal, three views")
    a1.legend(loc="upper right")

    a2.plot(t, log["p"], label="P term  Kp·e", color="tab:blue")
    a2.plot(t, log["i"], label="I term  Ki·∫e", color="tab:green")
    a2.plot(t, log["d"], label="D term  Kd·d(−y)/dt", color="tab:red")
    a2.plot(t, log["u"], "k", lw=1.0, label="total force u")
    a2.set(xlim=(0, 0.6), ylim=(-200, 320), xlabel="time [s]", ylabel="force [N]",
           title="What each term contributes")
    a2.legend(loc="upper right")
    save(fig, "fig02_pid_terms.png")


if __name__ == "__main__":
    main()
