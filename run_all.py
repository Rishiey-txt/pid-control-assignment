"""Recreate every figure (figures/) and every number (results/) in the report.

    python run_all.py
"""

import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "experiments"))

SCRIPTS = ["sec01_loop_diagram", "sec02_pid_terms", "sec03_plant", "sec04_metrics",
           "sec05_each_part", "sec06_compare", "sec07_real_world", "sec08_tuning",
           "sec09_final_demo"]

if __name__ == "__main__":
    t0 = time.time()
    for name in SCRIPTS:
        print(f"[{name}]")
        importlib.import_module(name).main()
    print(f"done in {time.time() - t0:.1f} s")
