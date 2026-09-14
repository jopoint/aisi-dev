import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.transforms import Affine2D

ROOM_W = 500
ROOM_H = 500
TABLE_W = 160
TABLE_H = 80

def add_table(ax, x, y, rot_deg, edgecolor="black", linewidth=2, label=None):
    # Rectangle is created around its center
    rect = Rectangle(
        (x - TABLE_W / 2, y - TABLE_H / 2),
        TABLE_W,
        TABLE_H,
        fill=False,
        edgecolor=edgecolor,
        linewidth=linewidth,
    )

    transform = (
        Affine2D()
        .rotate_deg_around(x, y, rot_deg)
        + ax.transData
    )
    rect.set_transform(transform)
    ax.add_patch(rect)

    if label:
        ax.text(x, y, label, ha="center", va="center")

def setup_ax(ax, title):
    ax.set_xlim(0, 500)
    ax.set_ylim(0, 500)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, 501, 100))
    ax.set_yticks(range(0, 501, 100))
    ax.grid(True, alpha=0.25)
    ax.set_title(title)
    ax.set_xlabel("x [cm]")
    ax.set_ylabel("y [cm]")

# Example: T3
fig, ax = plt.subplots(figsize=(7, 7))
setup_ax(ax, "T3A")

# Static tables
add_table(ax, 115, 150, 150, label="T1")
add_table(ax, 390, 125, 60, label="T2")
add_table(ax, 350, 430, 170, label="T3")

# Active table source
source = (120, 450, 0)
add_table(ax, *source, edgecolor="green", linewidth=3, label="Source")

# Active table target
target = (300, 210, 60)
add_table(ax, *target, edgecolor="blue", linewidth=3, label="Target")

# Movement arrow
ax.annotate(
    "",
    xy=(target[0], target[1]),
    xytext=(source[0], source[1]),
    arrowprops=dict(arrowstyle="->", linewidth=2)
)

# Participant start
participant = (240, 55)
circle = Circle(participant, 35, fill=False, edgecolor="red", linewidth=2)
ax.add_patch(circle)

plt.show()