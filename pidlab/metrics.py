"""The four step-response measures used throughout the report.

  rise time        : time to go from 10 % to 90 % of the final value
  overshoot        : how far the peak goes past the final value, in %
  settling time    : time after which y stays within +/-2 % of the final value
  steady-state err : setpoint minus final value
"""

import numpy as np


def step_metrics(t, y, setpoint=1.0, t0=0.0, band=0.02, tail=0.05):
    """Measures for a step applied at time t0. The final value is the mean of
    the last `tail` fraction of the record (the run must be long enough to settle)."""
    mask = t >= t0
    t, y = t[mask] - t0, y[mask]
    n_tail = max(1, int(len(y) * tail))
    y_final = float(np.mean(y[-n_tail:]))
    y0 = float(y[0])
    span = y_final - y0
    out = {"final": y_final, "sse": setpoint - y_final}

    # still oscillating at the end -> not a settled response
    if np.ptp(y[-n_tail:]) > band * abs(span) or abs(span) < 1e-9:
        out.update(rise=np.nan, overshoot=np.nan, settling=np.nan, peak=float(np.max(y)),
                   t_peak=float(t[np.argmax(y)]), t10=np.nan, t90=np.nan, settled=False)
        return out

    sgn = np.sign(span)
    z = (y - y0) * sgn                    # normalised so the response goes upward
    zf = abs(span)
    i10 = int(np.argmax(z >= 0.1 * zf))
    i90 = int(np.argmax(z >= 0.9 * zf))
    t10, t90 = _interp_cross(t, z, i10, 0.1 * zf), _interp_cross(t, z, i90, 0.9 * zf)
    ipk = int(np.argmax(z))
    overshoot = max(0.0, (z[ipk] - zf) / zf * 100)
    outside = np.abs(y - y_final) > band * abs(span)
    if outside.any():
        last = int(np.nonzero(outside)[0][-1])
        settling = float(t[min(last + 1, len(t) - 1)])
    else:
        settling = 0.0
    out.update(rise=t90 - t10, overshoot=overshoot, settling=settling,
               peak=float(y[ipk]), t_peak=float(t[ipk]), t10=t10, t90=t90, settled=True)
    return out


def _interp_cross(t, z, i, level):
    if i == 0:
        return float(t[0])
    z0, z1 = z[i - 1], z[i]
    return float(t[i - 1] + (level - z0) / (z1 - z0) * (t[i] - t[i - 1]))


def fmt_metrics(m):
    if not m.get("settled", True):
        return "does not settle"
    return (f"rise {m['rise']:.3f} s | overshoot {m['overshoot']:.1f} % | "
            f"settling {m['settling']:.3f} s | ss-error {m['sse']*1000:.1f} mm")
