"""Linear plants written as state-space models  x' = A x + B u,  y = C x.

Between controller updates the input u is held constant (zero-order hold), so
the plant can be advanced *exactly* with the matrix exponential. No ODE solver
error, and the result does not depend on a solver step size.
"""

import numpy as np


def expm(M):
    """Matrix exponential by scaling-and-squaring + Taylor series (NumPy only)."""
    norm = np.linalg.norm(M, ord=np.inf)
    s = max(0, int(np.ceil(np.log2(norm))) + 1) if norm > 0 else 0
    A = M / (2 ** s)
    result = np.eye(M.shape[0])
    term = np.eye(M.shape[0])
    for k in range(1, 20):
        term = term @ A / k
        result = result + term
    for _ in range(s):
        result = result @ result
    return result


class LinearPlant:
    def __init__(self, A, B, C, name="plant"):
        self.A = np.atleast_2d(np.asarray(A, dtype=float))
        self.B = np.asarray(B, dtype=float).reshape(-1, 1)
        self.C = np.asarray(C, dtype=float).reshape(1, -1)
        self.name = name
        self.n = self.A.shape[0]
        self.x = np.zeros(self.n)
        self._cache = {}

    def reset(self, x0=None):
        self.x = np.zeros(self.n) if x0 is None else np.asarray(x0, dtype=float)

    def _discretise(self, h):
        """Exact ZOH discretisation: x[k+1] = Ad x[k] + Bd u[k]."""
        if h not in self._cache:
            n = self.n
            M = np.zeros((n + 1, n + 1))
            M[:n, :n] = self.A * h
            M[:n, n:] = self.B * h
            E = expm(M)
            self._cache[h] = (E[:n, :n], E[:n, n])
        return self._cache[h]

    def step(self, u, h):
        Ad, Bd = self._discretise(h)
        self.x = Ad @ self.x + Bd * u

    def output(self):
        return float(self.C[0] @ self.x)


def mass_spring_damper(m=1.0, c=10.0, k=20.0):
    """m x'' + c x' + k x = F.   State = [position, velocity], output = position.

    Transfer function  X(s)/F(s) = 1 / (m s^2 + c s + k)
    """
    A = [[0.0, 1.0], [-k / m, -c / m]]
    B = [0.0, 1.0 / m]
    C = [1.0, 0.0]
    plant = LinearPlant(A, B, C, name=f"mass-spring-damper (m={m}, c={c}, k={k})")
    plant.m, plant.c, plant.k = m, c, k
    return plant


def third_order_lag():
    """G(s) = 1/(s+1)^3, built as three first-order lags in series."""
    A = [[-1.0, 0.0, 0.0],
         [1.0, -1.0, 0.0],
         [0.0, 1.0, -1.0]]
    B = [1.0, 0.0, 0.0]
    C = [0.0, 0.0, 1.0]
    return LinearPlant(A, B, C, name="1/(s+1)^3")
