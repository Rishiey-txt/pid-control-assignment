"""A reusable discrete-time PID controller, written from scratch.

The controller is called once every `dt` seconds with the current setpoint and
the current (possibly noisy) measurement, and returns the actuator command.

It contains the four practical fixes discussed in Section 7 of the report:

  * output limits + anti-windup   (problem a: actuator saturation / windup)
  * low-pass filtered derivative  (problem b: noisy sensor)
  * derivative on measurement     (problem c: derivative kick)
  * explicit sample time `dt`     (problem d: slow update rate is a parameter)

Each fix can be switched off so the problems can be reproduced.
"""

import math


class PID:
    def __init__(self, kp, ki=0.0, kd=0.0, dt=0.001,
                 u_min=-math.inf, u_max=math.inf,
                 anti_windup="backcalc", kb=None,
                 d_filter_tau=0.0, d_on_measurement=True):
        """
        kp, ki, kd        : gains.  u = kp*e + ki*integral(e) + kd*de/dt
        dt                : controller sample time [s]
        u_min, u_max      : actuator limits (same unit as u, e.g. N)
        anti_windup       : None, "clamp" (conditional integration) or
                            "backcalc" (back-calculation)
        kb                : back-calculation gain [1/s] (default ki/kp = 1/Ti)
        d_filter_tau      : time constant of the first-order low-pass filter on
                            the derivative [s]. 0 = no filter.
        d_on_measurement  : True  -> D acts on -dy/dt (no kick on setpoint steps)
                            False -> D acts on de/dt  (textbook form, kicks)
        """
        self.kp, self.ki, self.kd = kp, ki, kd
        self.dt = dt
        self.u_min, self.u_max = u_min, u_max
        if anti_windup not in (None, "clamp", "backcalc"):
            raise ValueError("anti_windup must be None, 'clamp' or 'backcalc'")
        self.anti_windup = anti_windup
        if kb is None:
            kb = (ki / kp) if (kp > 0 and ki > 0) else 0.0
        self.kb = kb
        self.d_filter_tau = d_filter_tau
        self.d_on_measurement = d_on_measurement
        self.reset()

    def reset(self):
        self.integral = 0.0        # integral term, stored directly in output units
        self.d_state = 0.0         # filtered derivative of the D input
        self.prev_input = None     # previous e (or -y) for the derivative
        # last computed terms, handy for plotting
        self.p_term = self.i_term = self.d_term = 0.0
        self.u_unsat = 0.0

    def update(self, setpoint, measurement):
        dt = self.dt
        error = setpoint - measurement

        # --- P: reacts to the present error
        p = self.kp * error

        # --- D: reacts to how fast the error is changing
        d_input = -measurement if self.d_on_measurement else error
        if self.prev_input is None:          # first call: no history yet
            self.prev_input = d_input
        raw_rate = (d_input - self.prev_input) / dt
        self.prev_input = d_input
        if self.d_filter_tau > 0:
            alpha = dt / (self.d_filter_tau + dt)      # first-order low-pass
            self.d_state += alpha * (raw_rate - self.d_state)
        else:
            self.d_state = raw_rate
        d = self.kd * self.d_state

        # --- I: reacts to the accumulated past error (rectangle rule)
        i_new = self.integral + self.ki * error * dt

        u_unsat = p + i_new + d
        u = min(max(u_unsat, self.u_min), self.u_max)

        # --- anti-windup
        if self.anti_windup == "clamp":
            pushing_up = u_unsat > self.u_max and error > 0
            pushing_down = u_unsat < self.u_min and error < 0
            if pushing_up or pushing_down:
                i_new = self.integral              # freeze the integrator
                u_unsat = p + i_new + d
                u = min(max(u_unsat, self.u_min), self.u_max)
        elif self.anti_windup == "backcalc":
            i_new += self.kb * (u - u_unsat) * dt  # bleed off the excess

        self.integral = i_new
        self.p_term, self.i_term, self.d_term = p, i_new, d
        self.u_unsat = u_unsat
        return u
