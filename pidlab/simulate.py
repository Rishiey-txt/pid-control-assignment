"""Closed-loop simulation: controller (sampled every Ts) + plant (exact ZOH).

The plant is advanced on a fine 'logging' grid (default 1 ms) so that the
continuous motion between slow controller updates is still visible in plots.
"""

import numpy as np


def step_setpoint(value=1.0, t_step=0.0):
    return lambda t: value if t >= t_step - 1e-12 else 0.0


def simulate(plant, controller, setpoint, t_end, Ts=None, h_log=1e-3,
             noise_amp=0.0, disturbance=None, seed=0):
    """
    plant        : LinearPlant (reset to zero at the start)
    controller   : PID (reset at the start); controller.dt must equal Ts
    setpoint     : float or function r(t)
    t_end        : simulated time [s]
    Ts           : controller sample time [s] (default controller.dt)
    h_log        : fine time step used to advance and log the plant [s]
    noise_amp    : uniform measurement noise in [-noise_amp, +noise_amp]
    disturbance  : optional function d(t) added to the plant input (e.g. a push)

    Returns a dict of NumPy arrays sampled every h_log.
    """
    if not callable(setpoint):
        sp_value = float(setpoint)
        setpoint = lambda t: sp_value
    Ts = controller.dt if Ts is None else Ts
    h = min(h_log, Ts)
    m = int(round(Ts / h))
    if abs(m * h - Ts) > 1e-9:
        raise ValueError("Ts must be an integer multiple of h_log")

    rng = np.random.default_rng(seed)
    plant.reset()
    controller.reset()

    n = int(round(t_end / h)) + 1
    log = {k: np.zeros(n) for k in
           ("t", "r", "y", "y_meas", "u", "u_unsat", "p", "i", "d")}
    u = 0.0
    y_meas = 0.0
    for j in range(n):
        t = j * h
        y = plant.output()
        if j % m == 0:                       # controller sample instant
            y_meas = y + (rng.uniform(-noise_amp, noise_amp) if noise_amp else 0.0)
            u = controller.update(setpoint(t), y_meas)
        log["t"][j] = t
        log["r"][j] = setpoint(t)
        log["y"][j] = y
        log["y_meas"][j] = y_meas
        log["u"][j] = u
        log["u_unsat"][j] = controller.u_unsat
        log["p"][j] = controller.p_term
        log["i"][j] = controller.i_term
        log["d"][j] = controller.d_term
        f = u + (disturbance(t) if disturbance else 0.0)
        plant.step(f, h)
    return log
