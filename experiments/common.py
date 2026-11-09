"""Shared settings and helpers for every experiment script."""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
FIG_DIR = os.path.join(ROOT, "figures")
RES_DIR = os.path.join(ROOT, "results")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RES_DIR, exist_ok=True)

# ---- the test system and final gains used across the report -------------
M, C, K = 1.0, 10.0, 20.0          # kg, N*s/m, N/m
SETPOINT = 1.0                      # m
DT = 0.001                          # controller sample time [s]
FINAL = dict(kp=300.0, ki=200.0, kd=20.0)   # chosen in Section 6
D_FILTER_TAU = 0.005                # derivative filter time constant [s] (Section 7b)
U_MAX = 30.0                        # actuator limit [N] (Section 7a)
NOISE = 0.001                       # sensor noise amplitude [m] (Section 7b)

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 200, "font.size": 9,
    "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.grid": True, "grid.alpha": 0.3, "lines.linewidth": 1.6,
    "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("  saved", os.path.relpath(path, ROOT))


def save_json(obj, name):
    path = os.path.join(RES_DIR, name)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=float)
    print("  saved", os.path.relpath(path, ROOT))


def r(x, n=3):
    """Round for tables; keeps NaN as None so JSON stays valid."""
    if x is None or x != x:
        return None
    return round(float(x), n)


def metrics_row(m):
    return {"rise_s": r(m["rise"]), "overshoot_pct": r(m["overshoot"], 1),
            "settling_s": r(m["settling"]), "sse_mm": r(m["sse"] * 1000, 1),
            "final_m": r(m["final"], 4), "peak_m": r(m["peak"], 4)}
