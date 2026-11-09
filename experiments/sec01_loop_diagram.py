"""Section 1 - the feedback loop drawn as a block diagram."""

from common import plt, save
from matplotlib.patches import FancyBboxPatch, Circle


def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02",
                                fc=color, ec="#333", lw=1.2))
    ax.text(x, y, text, ha="center", va="center", fontsize=9)


def arrow(ax, x0, y0, x1, y1, label=None, lx=0, ly=0.12):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#333"))
    if label:
        ax.text((x0 + x1) / 2 + lx, (y0 + y1) / 2 + ly, label, ha="center", fontsize=8,
                color="#444")


def main():
    fig, ax = plt.subplots(figsize=(7.4, 2.6))
    ax.set_xlim(0, 11.2)
    ax.set_ylim(-0.3, 2.3)
    ax.axis("off")
    ax.grid(False)

    ax.text(0.45, 1.5, "Target\n(setpoint r)", ha="center", va="center", fontsize=8.5)
    ax.add_patch(Circle((1.6, 1.5), 0.22, fc="white", ec="#333", lw=1.2))
    ax.text(1.6, 1.5, "Σ", ha="center", va="center", fontsize=11)
    ax.text(1.3, 1.72, "+", fontsize=9)
    ax.text(1.72, 1.08, "−", fontsize=11)
    box(ax, 4.6, 1.5, 3.0, 0.9, "Controller (PID)\nu = Kp·e + Ki·∫e dt + Kd·de/dt", "#dbe9f6")
    box(ax, 8.1, 1.5, 2.0, 0.9, "Machine (plant)\nblock-spring-damper", "#fde5cc")
    box(ax, 8.1, 0.15, 2.0, 0.6, "Sensor\n(measures position)", "#e2f0d9")

    arrow(ax, 0.95, 1.5, 1.38, 1.5)
    arrow(ax, 1.82, 1.5, 3.1, 1.5, "error\ne = r − y", ly=0.1)
    arrow(ax, 6.1, 1.5, 7.1, 1.5, "force\nu [N]", ly=0.1)
    arrow(ax, 9.1, 1.5, 11.1, 1.5, "position\ny [m]", lx=0.35, ly=0.1)
    ax.plot([9.9, 9.9], [1.5, 0.15], color="#333", lw=1.3)
    arrow(ax, 9.9, 0.15, 9.1, 0.15)
    ax.plot([7.1, 1.6], [0.15, 0.15], color="#333", lw=1.3)
    arrow(ax, 1.6, 0.15, 1.6, 1.28, "measured y", lx=-0.6, ly=0)
    ax.set_title("The feedback loop: measure, compare, correct, repeat")
    save(fig, "fig01_loop.png")


if __name__ == "__main__":
    main()
