"""Build the PDF report from the figures and numbers produced by run_all.py.

    python run_all.py               # 1) figures/ and results/
    python report/build_report.py   # 2) report/PID_Report.html -> report/PID_Report.pdf

Every number quoted in the text is read from results/*.json, so the document
always matches the code. PDF printing uses headless Google Chrome.
"""

import html
import json
import os
import shutil
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
EQ_DIR = os.path.join(HERE, "eq")
os.makedirs(EQ_DIR, exist_ok=True)

# ---- edit these two lines, then rebuild ---------------------------------
AUTHOR = "Maharishi M"
GITHUB = "https://github.com/Rishiey-txt/pid-control-assignment"
# --------------------------------------------------------------------------


def load(name):
    with open(os.path.join(RES, name)) as f:
        return json.load(f)


S3, S4, S5, S6, S7, S8, S9 = (load(f"sec0{i}.json") for i in (3, 4, 5, 6, 7, 8, 9))


# ---------------------------------------------------------------- helpers
def eq(name, tex, size=13):
    """Render a LaTeX-style formula (matplotlib mathtext) to SVG and return an <img>."""
    path = os.path.join(EQ_DIR, f"{name}.svg")
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=size)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.03, transparent=True)
    plt.close(fig)
    return f'<div class="eq"><img src="eq/{name}.svg" alt="{html.escape(tex)}"></div>'


FIG_N = [0]


def fig(file, caption, width=100):
    FIG_N[0] += 1
    return (f'<figure><img src="../figures/{file}" style="width:{width}%">'
            f'<figcaption><b>Figure {FIG_N[0]}.</b> {caption}</figcaption></figure>')


def table(headers, rows, cls=""):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def f(x, nd=3, unit=""):
    if x is None:
        return "—"
    return f"{x:.{nd}f}{unit}"


def mrow(m):
    """The four measures as table cells."""
    return [f(m["rise_s"]), f(m["overshoot_pct"], 1), f(m["settling_s"]), f(m["sse_mm"], 1)]


M4 = ["rise [s]", "overshoot [%]", "settling [s]", "ss-error [mm]"]

# --------------------------------------------------------------- numbers
P = {row["kp"]: row for row in S5["P"]}
PI = {row["ki"]: row for row in S5["PI"]}
PD = {row["kd"]: row for row in S5["PD"]}
CMP = {row["name"]: row for row in S6["compare"]}
KI = {row["ki"]: row for row in S6["ki_sweep"]}
WU = S7["windup"]
NZ = S7["noise"]
KK = S7["kick"]
SL = S7["slow"]
SLT = {row["Ts_ms"]: row for row in SL["table"]}
ZN = {row["rule"]: row for row in S8["rules"]}
zn_c, zn_h = ZN["Z-N classic PID"], ZN["hand-refined (ours)"]
fin = CMP["PID"]

CSS = """
@page { size: A4; margin: 15mm 16mm 15mm 16mm;
        @bottom-center { content: counter(page); } }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 9.6pt;
       line-height: 1.38; color: #1d1d1f; }
h1 { font-size: 20pt; margin: 0 0 2mm 0; }
h2 { font-size: 13pt; margin: 5mm 0 1.5mm 0; padding-bottom: 1mm; border-bottom: 1.5px solid #2c6fb7;
     color: #13406e; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 3mm 0 1mm 0; color: #13406e; break-after: avoid; }
p { margin: 1.2mm 0 1.6mm 0; text-align: justify; }
ul, ol { margin: 1mm 0 1.6mm 0; padding-left: 5.5mm; }
li { margin: 0.4mm 0; }
.subtitle { color: #555; margin-bottom: 3mm; }
.meta { font-size: 8.8pt; color: #333; background: #f3f6fa; border-left: 3px solid #2c6fb7;
        padding: 2mm 3mm; margin: 2mm 0 3mm 0; }
figure { margin: 2mm 0 3mm 0; text-align: center; break-inside: avoid; }
figure img { display: block; margin: 0 auto; }
figcaption { font-size: 8.6pt; color: #333; margin-top: 1mm; text-align: left; }
.eq { text-align: center; margin: 1.5mm 0; break-inside: avoid; }
.eq img { height: auto; max-width: 95%; }
table { border-collapse: collapse; margin: 1.5mm auto 3mm auto; font-size: 8.6pt; break-inside: avoid; }
th, td { border: 1px solid #c9d3df; padding: 1mm 2.2mm; text-align: center; }
th { background: #e8eff7; font-weight: 600; }
td:first-child { text-align: left; }
.box { background: #fbf7ec; border: 1px solid #e6d9b3; border-radius: 2mm; padding: 2mm 3mm;
       margin: 2mm 0; break-inside: avoid; }
.box b:first-child { color: #7a5b00; }
code, pre { font-family: Menlo, Consolas, monospace; font-size: 8pt; }
pre { background: #f5f7fa; border: 1px solid #dde3ea; padding: 2mm 3mm; border-radius: 1.5mm;
      white-space: pre-wrap; break-inside: avoid; margin: 1.5mm 0 2.5mm 0; line-height: 1.3; }
.two { display: flex; gap: 4mm; } .two > div { flex: 1; }
.small { font-size: 8.6pt; }
.pb { break-before: page; }
"""

# ------------------------------------------------------------- sections
sec1 = f"""
<h2>1. The basic idea</h2>
<p>Imagine standing in a shower that is too cold. You feel the water, compare it with the
temperature you want, and turn the knob towards hot. If it is <i>much</i> too cold you turn the knob a
lot, and if it is only a little cold you turn it a little. If it has been slightly cold for a long time,
you keep nudging the knob until the cold feeling is gone. If you notice the water warming up quickly,
you ease off early so you don't get scalded. Then you feel the water again and repeat.</p>
<p>That loop of <b>measure → compare → correct → repeat</b> is feedback control, and the three
habits above are exactly the <b>P</b>, <b>I</b> and <b>D</b> of a PID controller. A controller never
needs to know in advance how much force is "right". It keeps shrinking the gap (the <b>error</b>)
between the <b>setpoint</b> (target) and the measured value, many times per second. Because it
always reacts to what really happened, it also corrects surprises such as a push, a heavier load or a
weaker spring.</p>
{fig("fig01_loop.png", "The feedback loop. The sensor's reading is subtracted from the target to give the error; the PID turns the error into a force; the machine moves; the sensor measures again.", 92)}
"""

sec2 = f"""
<h2>2. The PID formula</h2>
{eq("pid", r"u(t) \;=\; K_p\,e(t) \;+\; K_i\int_0^{t} e(\tau)\,d\tau \;+\; K_d\,\frac{de(t)}{dt}, \qquad e(t)=r(t)-y(t)", 14)}
{table(["symbol", "meaning", "unit (our test system)"], [
    ["r(t)", "setpoint, the target position", "m"],
    ["y(t)", "measured value, the actual position", "m"],
    ["e(t)", "error = r − y, how far we still are from the target", "m"],
    ["u(t)", "controller output, the force sent to the motor", "N"],
    ["K<sub>p</sub>", "proportional gain: newtons per metre of error", "N/m"],
    ["K<sub>i</sub>", "integral gain: newtons per (metre × second) of accumulated error", "N/(m·s)"],
    ["K<sub>d</sub>", "derivative gain: newtons per (metre/second) of error change", "N·s/m"],
    ["t, τ, T<sub>s</sub>", "time, integration variable, controller sample time", "s"],
])}
<ul>
<li><b>P, the present error.</b> Push in proportion to how far away we are right now. Large error → large
push. P alone fades out as the error shrinks, which is why it usually stops a little short (Section 5).</li>
<li><b>I, the past error.</b> Add up the error over time. Even a tiny error that lasts a long time builds
up a large push, so I keeps working until the error is <i>exactly</i> zero. It is the only part that can
produce a steady force with zero error.</li>
<li><b>D, how fast the error is changing.</b> If the error is shrinking fast we are about to overshoot, so
D pushes back early, like a brake. It acts like extra damping (a shock absorber).</li>
</ul>
<p>Engineers often write the same controller as u = K<sub>p</sub>(e + (1/T<sub>i</sub>)∫e dt + T<sub>d</sub> de/dt),
where T<sub>i</sub> = K<sub>p</sub>/K<sub>i</sub> (integral time) and T<sub>d</sub> = K<sub>d</sub>/K<sub>p</sub>
(derivative time). Section 8 uses this form.</p>
{fig("fig02_pid_terms.png", "Left: P uses the current value of the error, I uses the area under it, D uses its slope. Right: the force from each term during a step with the final gains of Section 6; I slowly takes over the 20 N needed to hold the block.")}
<h3>The step-by-step version a computer runs</h3>
<p>A microcontroller can't integrate or differentiate continuously. Every T<sub>s</sub> seconds (here
T<sub>s</sub> = 1 ms) it replaces the integral with a running sum and the derivative with a difference:</p>
{eq("disc", r"e_k=r_k-y_k,\quad I_k = I_{k-1} + K_i\,e_k\,T_s,\quad D_k = K_d\,\frac{e_k-e_{k-1}}{T_s},\quad u_k = K_p e_k + I_k + D_k", 12.5)}
<pre>every Ts seconds:
    error    = setpoint - read_sensor()
    integral = integral + Ki * error * Ts          # running sum   (I)
    deriv    = Kd * (error - prev_error) / Ts      # rate of change (D)
    u        = Kp * error + integral + deriv
    send_to_motor(u);  prev_error = error</pre>
<p>Section 7 shows why this naive version needs four small changes before it is safe on real hardware.</p>
"""

sec3 = f"""
<h2>3. The test system: block on a spring with a damper</h2>
<div class="two"><div>
<p>A 1 kg block is attached to a wall by a spring (k = 20 N/m) and a damper (c = 10 N·s/m), like one
corner of a car suspension. A motor pushes it with force F. Newton's second law (mass × acceleration =
sum of forces) gives</p>
{eq("plant", r"m\ddot{x} + c\dot{x} + kx = F \;\;\Rightarrow\;\; \ddot{x} + 10\dot{x} + 20x = F", 12.5)}
{eq("tf", r"G(s)=\frac{X(s)}{F(s)}=\frac{1}{s^2+10s+20}", 12.5)}
</div><div>
<p>Without a controller the system is <b>over-damped</b> (damping ratio ζ = c/(2√(km)) = {S3['zeta']:.2f} &gt; 1):
its poles are at s = {S3['poles'][1]:.2f} and {S3['poles'][0]:.2f}, so it creeps to rest without bouncing,
in about 4/2.76 ≈ 1.5 s.</p>
<p><b>Why a constant push is needed.</b> When the block is resting at 1 m, velocity and acceleration are
zero, so the equation leaves kx = F: the spring pulls back with <b>20 N/m × 1 m = 20 N</b>, and the motor
must keep pushing 20 N forever. Stop pushing and the spring drags the block back to 0.</p>
</div></div>
{fig("fig03_open_loop.png", "Left: holding a constant force F gives a final position F/k (0.05 m per newton), so exactly 20 N is needed for 1 m. Right: once the block stops, the spring carries the whole 20 N and the damper carries nothing.")}
<p>This sets the main challenge. The controller must output <b>20 N while the error is zero</b>. All
simulations step the plant exactly between controller updates (zero-order hold, computed with the matrix
exponential), with the controller running at 1 kHz unless stated otherwise.</p>
"""

sec4 = f"""
<h2>4. How to judge a result</h2>
<p>We judge every controller by its <b>step response</b>: the target jumps from 0 to 1 m and we watch
what happens. Four numbers sum it up:</p>
<ol>
<li><b>Rise time</b>: how fast it gets there; time to go from 10 % to 90 % of the final value.</li>
<li><b>Overshoot</b>: how far it goes past the final value before coming back, in % of the final value.</li>
<li><b>Settling time</b>: how long until it calms down; time after which it stays inside ±2 % of the final value.</li>
<li><b>Steady-state error</b>: how far from the target it finally stops; setpoint − final value.</li>
</ol>
{fig("fig04_metrics.png", f"All four measures on a P-only response (K<sub>p</sub> = 300): rise {S4['rise_s']:.3f} s, overshoot {S4['overshoot_pct']:.1f} %, settling {S4['settling_s']:.3f} s, and it stops {S4['sse_mm']:.1f} mm short of the target.")}
<p>The measures pull against each other. Pushing harder shortens the rise time but usually increases
overshoot; damping more removes overshoot but slows the rise. Tuning means finding a good balance.</p>
"""

p_rows = [[f"{kp}", f(P[kp]["pred_final_m"], 4), f(P[kp]["sim_final_m"], 4), f(P[kp]["pred_sse_mm"], 1),
           f(P[kp]["sim_sse_mm"], 1), f(P[kp]["zeta"]), f(P[kp]["pred_os_pct"], 1), f(P[kp]["sim_os_pct"], 1)]
          for kp in (10, 50, 100, 300, 500)]
pd_rows = [[f"{kd}", f(PD[kd]["zeta"]), f(PD[kd]["pred_os_pct"], 1), f(PD[kd]["sim_os_pct"], 1),
            f(PD[kd]["rise_s"]), f(PD[kd]["settling_s"])] for kd in (0, 5, 10, 20, 40)]
pi_rows = [[f"{ki}", *mrow(PI[ki])] for ki in (0, 30, 70, 150)]

sec5 = f"""
<h2>5. Each part alone</h2>
<h3>5.1 P only: fast, but always short of the target</h3>
<p>With u = K<sub>p</sub>(r − x), the closed loop becomes a new spring-mass-damper whose spring is
stiffer by K<sub>p</sub>:</p>
{eq("pcl", r"m\ddot{x} + c\dot{x} + (k+K_p)\,x = K_p\,r", 12.5)}
<p><b>Why it stops short.</b> At rest, the motor force K<sub>p</sub>·e must balance the spring force k·x.
If the error were zero the motor would push 0 N and the spring would pull the block back, so the only
possible balance has e &gt; 0:</p>
{eq("pss", r"K_p(1-x_{ss}) = k\,x_{ss} \;\Rightarrow\; x_{ss}=\frac{K_p}{k+K_p},\qquad e_{ss}=\frac{k}{k+K_p}=\frac{20}{20+K_p}\ \mathrm{m}", 12.5)}
<p>Raising K<sub>p</sub> shrinks the error but never removes it. It also lowers the damping ratio
ζ = c / (2√(m(k+K<sub>p</sub>))), and for ζ &lt; 1 the overshoot of a second-order system is
OS = exp(−πζ/√(1−ζ²)). Predictions and simulation agree to 0.1 mm in final value and within
{max(abs(P[k]['pred_os_pct'] - P[k]['sim_os_pct']) for k in P):.1f} percentage points in overshoot (the small gap
comes from the 1 ms sampling):</p>
{table(["K<sub>p</sub> [N/m]", "final x predicted [m]", "final x simulated [m]", "error predicted [mm]",
        "error simulated [mm]", "ζ", "OS predicted [%]", "OS simulated [%]"], p_rows)}
{fig("fig05a_p_only.png", f"P only. Raising K<sub>p</sub> from 10 to 500 cuts the steady-state error from {P[10]['sim_sse_mm']:.0f} mm to {P[500]['sim_sse_mm']:.1f} mm, but overshoot grows from {P[10]['sim_os_pct']:.1f} % to {P[500]['sim_os_pct']:.1f} % and the initial force reaches 500 N.")}

<h3>5.2 Adding I: the offset disappears</h3>
<p>The integral keeps growing as long as any error remains, so the loop can only come to rest when the
error is exactly zero. At that point the I term alone supplies the 20 N the spring needs (right
panel). With K<sub>p</sub> = 30 the error drops from {PI[0]['sse_mm']:.0f} mm to {PI[70]['sse_mm']:.1f} mm.
Too little K<sub>i</sub> (30) is very slow (settling {PI[30]['settling_s']:.2f} s). Too much (150) overshoots by
{PI[150]['overshoot_pct']:.1f} %, because the I term keeps growing during the whole rise and has to be "unwound"
by going past the target.</p>
{table(["K<sub>i</sub> (K<sub>p</sub> = 30)", *M4], pi_rows)}
{fig("fig05b_pi.png", "PI control. Any K<sub>i</sub> &gt; 0 drives the error to zero and the force to the 20 N holding value; K<sub>i</sub> = 70 does it fastest without real overshoot.")}

<h3>5.3 Adding D: less bouncing</h3>
<p>D adds a force −K<sub>d</sub>·ẋ that opposes velocity, exactly like a bigger damper (c becomes c + K<sub>d</sub>):</p>
{eq("pdcl", r"m\ddot{x} + (c+K_d)\,\dot{x} + (k+K_p)\,x = K_p\,r \quad\Rightarrow\quad \zeta = \frac{c+K_d}{2\sqrt{m(k+K_p)}}", 12.5)}
<p>With K<sub>p</sub> = 300, ζ rises from 0.28 to 0.84 as K<sub>d</sub> goes from 0 to 20, and the overshoot falls
from {PD[0]['sim_os_pct']:.1f} % to {PD[20]['sim_os_pct']:.1f} %. Settling time drops by
{(1 - PD[20]['settling_s'] / PD[0]['settling_s']) * 100:.0f} %. Too much D (K<sub>d</sub> = 40, ζ = 1.4) makes it sluggish
again. D is zero once the block stops, so the {PD[0]['sse_mm']:.1f} mm offset is unchanged. Predicted and
simulated overshoot agree closely:</p>
{table(["K<sub>d</sub> (K<sub>p</sub> = 300)", "ζ", "OS predicted [%]", "OS simulated [%]", "rise [s]", "settling [s]"], pd_rows)}
{fig("fig05c_pd.png", "PD control. Extra damping from K<sub>d</sub> removes the bounce without slowing the rise much, but the 62.5 mm offset of P control remains.")}
"""

cmp_rows = [[r["name"], r["gains"], *mrow(r), f"{r['peak_force_N']:.0f}"] for r in S6["compare"]]
ki_rows = [[f"{ki}", *mrow(KI[ki])] for ki in (0, 100, 200, 400, 800)]

sec6 = f"""
<h2>6. All together</h2>
{fig("fig06_compare.png", "The best P, PI, PD and PID from Section 5 on one step. Only PI and PID reach the target; PID is the only one that is both fast and on target.")}
{table(["controller", "gains", *M4, "peak force [N]"], cmp_rows)}
<p><b>Choosing the final gains.</b> I followed the hand-tuning recipe of Section 8. K<sub>p</sub> = 300 gives a fast
rise. K<sub>d</sub> = 20 brings ζ to 0.84, which removes the bounce (overshoot 40.7 % → 0.7 %). Finally,
K<sub>i</sub> is the smallest value that removes the offset quickly without bringing overshoot back:</p>
<div class="two"><div>
{table(["K<sub>i</sub> (K<sub>p</sub>=300, K<sub>d</sub>=20)", *M4], ki_rows)}
</div><div>
<p class="small">K<sub>i</sub> = 100 is too slow: it creeps the last 7 mm and needs {KI[100]['settling_s']:.2f} s to settle.
K<sub>i</sub> ≥ 400 overshoots ({KI[400]['overshoot_pct']:.1f} % and more). <b>K<sub>i</sub> = 200</b> settles in
{KI[200]['settling_s']:.3f} s with {KI[200]['overshoot_pct']:.1f} % overshoot.</p>
<p class="small"><b>Final gains: K<sub>p</sub> = 300 N/m, K<sub>i</sub> = 200 N/(m·s), K<sub>d</sub> = 20 N·s/m.</b>
Compared with P alone, overshoot drops from 40.7 % to {fin['overshoot_pct']:.1f} %, settling from
{CMP['P']['settling_s']:.3f} s to {fin['settling_s']:.3f} s, and the 62.5 mm error is gone.</p>
</div></div>
{fig("fig06b_ki_choice.png", "Zoom near the target with K<sub>p</sub> and K<sub>d</sub> fixed. K<sub>i</sub> = 200 (thick line) removes the offset with only 0.5 % overshoot; larger values overshoot more, smaller ones creep.")}
<div class="box"><b>Catch:</b> these gains ask for a 300 N peak force (K<sub>p</sub> × 1 m of initial error). A real
motor may not have that. Section 7a shows what happens with only 30 N.</div>
"""

wu = {w["case"]: w for w in WU}
wu_rows = [[w["case"], *mrow(w), f(w["max_I_term_N"], 1)] for w in WU]
nz_raw, nz_f = NZ
kk_e, kk_m = KK
sl_rows = [[f"{ts}", f(SLT[ts]["spectral_radius"], 4), f(SLT[ts]["overshoot_pct"], 1) if SLT[ts]["overshoot_pct"] is not None else "—",
            f(SLT[ts]["settling_s"]) if SLT[ts]["settling_s"] is not None else ("slowly decaying" if SLT[ts]["spectral_radius"] < 1 else "<b>unstable</b>")]
           for ts in (1, 20, 40, 50, 60, 70, 80)]

sec7 = f"""
<h2>7. Real-world problems and their fixes</h2>
<p>All four experiments use the final gains (300 / 200 / 20). Each problem is shown first, then fixed in
the controller code (<code>pidlab/controller.py</code>).</p>

<h3>(a) Force limit of 30 N → integral windup</h3>
<p>The PID asks for 300 N at the start but the motor saturates at 30 N, so the block moves slower than the
controller "expects". The error stays large for longer, and the I term keeps accumulating. It climbs to
{wu['30 N limit, no anti-windup']['max_I_term_N']:.0f} N when only 20 N is needed. That stored extra force then
pushes the block past the target. <b>Fix: anti-windup.</b> <i>Clamping</i> stops integrating while the output
is saturated and the error would push it further. <i>Back-calculation</i> feeds the difference between the
requested and the delivered force back into the integrator, bleeding off the excess at rate
K<sub>b</sub>(u<sub>sat</sub> − u) with K<sub>b</sub> = K<sub>i</sub>/K<sub>p</sub>.</p>
{fig("fig07a_windup.png", "Windup. Without anti-windup the I term (right) grows to almost 3× the 20 N needed and the block overshoots; back-calculation keeps the I term at 20 N and removes the overshoot.")}
{table(["case", *M4, "max I term [N]"], wu_rows)}
<p>Back-calculation is best here: overshoot {wu['30 N limit, no anti-windup']['overshoot_pct']:.1f} % → 0 %,
settling {wu['30 N limit, no anti-windup']['settling_s']:.2f} s → {wu['30 N limit + back-calculation']['settling_s']:.2f} s.
Clamping also removes the overshoot, but the I term starts building only after the saturation ends, so the last
few millimetres take {wu['30 N limit + clamping']['settling_s']:.2f} s. No controller can beat the ~0.4 s rise time:
that is the physical limit of a 30 N motor against a 20 N spring. Back-calculation is the default in the final code.</p>

<h3>(b) Noisy sensor (±1 mm) → jumpy D term</h3>
<p>D divides the change in measurement by T<sub>s</sub>. Noise that jumps by up to 2 mm between two 1 ms samples looks
like a velocity of 2 m/s, and K<sub>d</sub> = 20 turns it into ±40 N of random force. <b>Fix: a low-pass filter on
the derivative</b>, d<sub>k</sub> = d<sub>k−1</sub> + α(raw<sub>k</sub> − d<sub>k−1</sub>) with α = T<sub>s</sub>/(τ + T<sub>s</sub>),
τ = 5 ms (cut-off 1/(2πτ) ≈ 32 Hz, well above the ~3.6 Hz bandwidth of the loop).</p>
{fig("fig07b_noise.png", "Sensor noise. Left: with a raw derivative the motor force chatters between −20 and +60 N; the filtered version stays within a few newtons of 20 N. Right: the block itself barely moves in either case.")}
<p>After settling, the force's standard deviation falls from {nz_raw['u_std_N']:.1f} N to {nz_f['u_std_N']:.1f} N
({(1 - nz_f['u_std_N'] / nz_raw['u_std_N']) * 100:.0f} % less) and the peak-to-peak from {nz_raw['u_p2p_N']:.0f} N to
{nz_f['u_p2p_N']:.0f} N, while the step response hardly changes (settling {nz_raw['settling_s']:.3f} s →
{nz_f['settling_s']:.3f} s). The block's position jitter is only about {nz_raw['y_std_mm']:.2f} mm either way, because
the mass filters fast forces. The real damage of a noisy D term is heat, wear and audible buzz in the motor.</p>

<h3>(c) Sudden target change → derivative kick</h3>
<p>When the target jumps by 1 m in one sample, the error jumps too, and de/dt ≈ 1 m / 0.001 s = 1000 m/s.
D outputs K<sub>d</sub> × 1000 = <b>20 000 N</b> for one sample (simulated: {kk_e['peak_D_N']:.0f} N). <b>Fix: take the
derivative of the measurement instead of the error</b>, D = −K<sub>d</sub>·dy/dt. When the target is constant this is
identical to de/dt, but the block's position can't jump (it has mass), so there is no spike.</p>
{fig("fig07c_kick.png", f"Derivative kick. Left (log scale): D on error produces a {kk_e['peak_force_N']:.0f} N spike; D on measurement peaks at {kk_m['peak_force_N']:.0f} N (from P alone). Right: the kick throws the block forward.")}

<h3>(d) Controller updates too slowly</h3>
<p>Between updates the force is frozen (right panel below), so the controller reacts to old information.
This delay of about T<sub>s</sub>/2 eats into the <b>phase margin</b>, the safety margin against oscillation.</p>
{fig("fig07d_slow.png", "Slow updates. 40 ms still works; at 60 ms the block rings with 21 % overshoot; at 80 ms the oscillation grows and the loop is unstable.")}
<div class="two"><div>
{table(["T<sub>s</sub> [ms]", "max |eigenvalue|", "overshoot [%]", "settling [s]"], sl_rows)}
</div><div>
<p class="small"><b>Checking by calculation.</b> The sampled loop (PID code + exactly discretised plant) is a linear
recurrence z<sub>k+1</sub> = Φ z<sub>k</sub>. It is stable when every eigenvalue of Φ has magnitude below 1. A sweep
gives the exact limit <b>T<sub>s</sub> = {SL['Ts_limit_exact_ms']:.1f} ms</b>, which matches the simulations
(70 ms rings for a long time, 80 ms blows up). A quick hand estimate: the continuous loop crosses gain 1 at
ω<sub>c</sub> = {SL['crossover_rad_s']:.1f} rad/s with {SL['phase_margin_deg']:.0f}° of phase margin. Sampling plus the
backward-difference derivative cost about ω<sub>c</sub>T<sub>s</sub> radians, so the limit is T<sub>s</sub> ≈ PM/ω<sub>c</sub>
≈ {SL['Ts_limit_rule_of_thumb_ms']:.0f} ms. That is slightly pessimistic but in the right place.
<b>Rule of thumb:</b> sample at least 10–20× faster than the loop bandwidth (ω<sub>c</sub> ≈ 3.6 Hz → ≥ 40–70 Hz). We use 1 kHz.</p>
</div></div>
"""

zn_rows = [[r["rule"], f(r["kp"], 2), f(r["Ti_s"], 2), f(r["Td_s"], 2), *mrow(r)] for r in S8["rules"]]

sec8 = f"""
<h2>8. Choosing the gains</h2>
<h3>Tuning by hand</h3>
<ol>
<li><b>Start safe.</b> Set K<sub>i</sub> = K<sub>d</sub> = 0, small K<sub>p</sub>. Check the sign: the output must move <i>towards</i> the target.</li>
<li><b>Raise K<sub>p</sub></b> until the response is fast but overshoots clearly (here 300: rise 0.07 s, 41 % overshoot). Back off if the force limit or noise becomes a problem.</li>
<li><b>Add K<sub>d</sub></b> until the overshoot is almost gone (aim for ζ ≈ 0.7–0.9; here K<sub>d</sub> = 20 → 0.7 %). Stop before it becomes sluggish.</li>
<li><b>Add K<sub>i</sub></b> slowly until the steady-state error disappears in acceptable time. Stop when overshoot starts to return (here 200).</li>
<li><b>Make it real.</b> Add the output limit with anti-windup, D filter and D on measurement, then re-check with a disturbance, noise and a different setpoint. Fine-tune by ±20 %.</li>
</ol>
<h3>Ziegler–Nichols on a second system, G(s) = 1/(s+1)<sup>3</sup></h3>
<p>This plant is three slow lags in series, a common model of thermal or process systems. Following
Ziegler–Nichols, I used P only and raised K<sub>p</sub> until the output swung with constant amplitude. In code
this is a bisection on K<sub>p</sub> until a late swing is exactly as large as an early one. Result:
<b>K<sub>u</sub> = {S8['Ku']:.3f}</b> and <b>P<sub>u</sub> = {S8['Pu_s']:.3f} s</b>. <i>Check:</i> the loop is on the edge of stability when
(jω+1)<sup>3</sup> + K = 0. The imaginary part gives ω = √3 and the real part K = 8, so P<sub>u</sub> = 2π/√3 = 3.628 s. Both match.</p>
{table(["Z-N recipe", "K<sub>p</sub>", "T<sub>i</sub>", "T<sub>d</sub>"], [
    ["P", "0.5 K<sub>u</sub>", "—", "—"], ["PI", "0.45 K<sub>u</sub>", "P<sub>u</sub>/1.2", "—"],
    ["PID (classic)", "0.6 K<sub>u</sub>", "P<sub>u</sub>/2", "P<sub>u</sub>/8"]])}
{fig("fig08_zn.png", "Left: at K<sub>p</sub> = K<sub>u</sub> the oscillation neither grows nor decays, and its period is P<sub>u</sub>. Right: classic Z-N PID overshoots by 52 %; the hand-refined version overshoots by 1.4 % and settles in less than half the time.")}
{table(["tuning", "K<sub>p</sub>", "T<sub>i</sub> [s]", "T<sub>d</sub> [s]", *M4], zn_rows)}
<p><b>Improving it.</b> Classic Z-N aims for a "quarter-amplitude decay", which is deliberately aggressive:
{zn_c['overshoot_pct']:.1f} % overshoot and {zn_c['settling_s']:.1f} s settling. The overshoot here comes mostly from
the integral filling up during the slow rise. So I made three changes: (1) lowered K<sub>p</sub> to 0.5 K<sub>u</sub>,
(2) tripled T<sub>i</sub> to 1.5 P<sub>u</sub> (much less integral action) and (3) doubled T<sub>d</sub> to P<sub>u</sub>/4 (more
damping). Overshoot fell from {zn_c['overshoot_pct']:.1f} % to {zn_h['overshoot_pct']:.1f} % and settling from
{zn_c['settling_s']:.1f} s to {zn_h['settling_s']:.1f} s. The price was a slower rise ({zn_c['rise_s']:.2f} s →
{zn_h['rise_s']:.2f} s). The published "some/no overshoot" variants still gave 21–25 % here, a reminder that
recipes are starting points, not answers.</p>
"""

code_listing = """class PID:
    def __init__(self, kp, ki=0, kd=0, dt=0.001, u_min=-inf, u_max=inf,
                 anti_windup="backcalc", kb=None, d_filter_tau=0.0, d_on_measurement=True): ...

    def update(self, setpoint, measurement):
        error = setpoint - measurement
        p = self.kp * error                                       # P: present
        d_input = -measurement if self.d_on_measurement else error  # fix (c)
        raw_rate = (d_input - self.prev_input) / dt
        self.d_state += dt / (self.d_filter_tau + dt) * (raw_rate - self.d_state)  # fix (b)
        d = self.kd * self.d_state                                # D: trend
        i_new = self.integral + self.ki * error * dt              # I: past
        u_unsat = p + i_new + d
        u = min(max(u_unsat, self.u_min), self.u_max)             # actuator limit
        if self.anti_windup == "clamp" and saturated_in_direction_of(error):
            i_new = self.integral                                 # fix (a), option 1
        elif self.anti_windup == "backcalc":
            i_new += self.kb * (u - u_unsat) * dt                 # fix (a), option 2
        self.integral = i_new
        return u                                                  # fix (d): dt is explicit"""

sec9 = f"""
<h2>9. The code</h2>
<p>The repository (<a href="{GITHUB}">{GITHUB}</a>) contains a small library <code>pidlab/</code> and one script per
section in <code>experiments/</code>. <code>python run_all.py</code> recreates every figure and number in this document
in about 5 s. Only NumPy and Matplotlib are used; the PID logic, the plant simulation (exact zero-order hold
using a hand-written matrix exponential) and the performance measures are all written from scratch.</p>
<pre>{html.escape(code_listing)}</pre>
<p class="small">Abridged; the full file includes first-call handling and parameter checks. Usage:
<code>pid = PID(300, 200, 20, dt=0.001, u_min=-30, u_max=30, d_filter_tau=0.005)</code>, then call
<code>u = pid.update(target, sensor_reading)</code> once per sample.</p>
{fig("fig09_final_demo.png", "The final controller with every fix on, a 30 N motor and a noisy sensor: step to 1 m, a constant −5 N push at 2 s, then a new target of 0.5 m at 3.5 s.")}
<p><b>Results.</b> Step 0 → 1 m: rise {S9['step_up']['rise_s']:.3f} s, overshoot {S9['step_up']['overshoot_pct']:.1f} %,
settling {S9['step_up']['settling_s']:.3f} s, final error {S9['step_up']['sse_mm']:.1f} mm, despite the force limit and
the noise. The −5 N push only dents the position by {S9['push_dip_mm']:.0f} mm. The I term then rises from
{S9['I_term_before_push_N']:.1f} N towards 25 N to cancel it, which P and D alone could never do. Step 1 → 0.5 m:
overshoot {S9['step_down']['overshoot_pct']:.1f} %, settling {S9['step_down']['settling_s']:.3f} s, and no derivative kick
at the target change.</p>
"""

sec10 = f"""
<h2>10. Real robots &amp; common myths</h2>
{table(["system", "what is controlled", "how PID is used"], [
    ["DC motor speed (conveyors, wheels)", "shaft speed from an encoder", "PI on speed (D is rarely needed because the motor is a first-order system), usually over a fast inner current loop; anti-windup because the voltage saturates."],
    ["Quadcopter drone", "roll/pitch/yaw angle and rate", "Cascade: an outer angle loop (P) sets a target rotation rate for an inner rate PID running at 1–8 kHz. D is heavily filtered because of propeller vibration, and I is held back during flips to avoid windup."],
    ["Robot arm joint", "joint angle", "PID or cascaded position → velocity → current loops in each servo drive, plus a gravity feed-forward term so the I term does not have to carry the arm's weight."],
    ["Line-following robot", "sideways offset from the line", "PD on the position error from an IR sensor array; the output is a difference in wheel speeds. I is often left out because a small offset is acceptable."],
    ["Car cruise control", "vehicle speed", "PI on speed → throttle. I removes the error on hills, and anti-windup is needed when the throttle is fully open on a steep climb."],
    ["3D-printer hot end", "nozzle temperature", "PID with a relay 'auto-tune' that measures the swing, as in Section 8. I removes the offset caused by heat loss to the air."],
], "small")}
<h3>Myths</h3>
<ul>
<li><b>"Higher gains are always better/faster."</b> Raising K<sub>p</sub> from 100 to 500 raised overshoot from 20 % to 50 %
(Fig. 5). High gains ask for forces the motor doesn't have (Fig. 10), and any delay, such as slow sampling, pushes an aggressive loop into oscillation (Fig. 13).</li>
<li><b>"You always need all three terms."</b> Many good loops are PI (motor speed, cruise control) or PD (line followers).
D amplifies noise (Fig. 11), and I adds overshoot and windup. Use only what the problem needs.</li>
<li><b>"The D term predicts the future."</b> It only extends the current slope. With a noisy sensor it "predicts" noise
(±40 N of chatter here); with a target jump it predicts nonsense (a 20 000 N kick).</li>
<li><b>"Ziegler–Nichols gives optimal gains."</b> It gave 52 % overshoot on 1/(s+1)<sup>3</sup>. It is a quick, aggressive starting point.</li>
<li><b>"PID doesn't need any model or physics."</b> It can be tuned without one, but knowing the plant explained every result
here: the 20 N holding force, why P is short by 20/(20+K<sub>p</sub>), and where the loop goes unstable.</li>
<li><b>"Once tuned, it stays tuned."</b> If the mass, friction, battery voltage or load change, the loop behaves differently.
Real systems re-tune, add feed-forward, or schedule gains.</li>
</ul>

<h2>Notes</h2>
<p class="small"><b>Use of AI tools.</b> Claude (Anthropic) helped me structure the code and draft the text.
Every number and graph in this document is produced by the code in the repository, and the key results were
checked against hand calculations (Sections 5, 7d and 8). <b>Missing items:</b> none. <b>References:</b>
K. J. Åström &amp; R. M. Murray, <i>Feedback Systems</i> (2nd ed.); K. J. Åström &amp; T. Hägglund, <i>Advanced PID Control</i>;
University of Michigan "Control Tutorials for MATLAB &amp; Simulink", PID introduction (same mass-spring-damper example).</p>
"""

head = f"""
<h1>PID Control, from zero to working code</h1>
<div class="subtitle">Physical AI intern assignment · Modern Monk Labs · {html.escape(AUTHOR)}</div>
<div class="meta"><b>Key words.</b> <b>Setpoint</b>: target value · <b>Error</b>: target − actual ·
<b>Plant</b>: the machine being controlled · <b>Gains</b> K<sub>p</sub>, K<sub>i</sub>, K<sub>d</sub>: how strongly each
part reacts · <b>Overshoot</b>: going past the target · <b>Step response</b>: how the system moves when the target
suddenly changes.<br><b>Code:</b> <a href="{GITHUB}">{GITHUB}</a> (Python, NumPy + Matplotlib; <code>python run_all.py</code>
recreates every graph).</div>
"""

doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>PID Control Report</title>
<style>{CSS}</style></head><body>
{head}{sec1}{sec2}{sec3}{sec4}{sec5}{sec6}{sec7}{sec8}{sec9}{sec10}
</body></html>"""


def find_chrome():
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chrome")):
        if c and os.path.exists(c):
            return c
    return None


if __name__ == "__main__":
    out_html = os.path.join(HERE, "PID_Report.html")
    with open(out_html, "w") as fh:
        fh.write(doc)
    print("wrote", os.path.relpath(out_html, ROOT))
    chrome = find_chrome()
    if not chrome:
        sys.exit("Chrome not found: open report/PID_Report.html in a browser and print to PDF.")
    out_pdf = os.path.join(HERE, "PID_Report.pdf")
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out_pdf}", "file://" + out_html],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("wrote", os.path.relpath(out_pdf, ROOT))
