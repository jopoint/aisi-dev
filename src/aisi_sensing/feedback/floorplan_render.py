from __future__ import annotations

from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
from ..core.types import DetectedEntity, FrameEvent



def draw_floorplan(ax, frame: FrameEvent, title: Optional[str] = None) -> None:
    """Draw a simple top-down scatter plot of furniture and people on the given axes."""
    furn = frame.furniture
    peep = frame.people
    fx = [e.pose.x for e in furn]
    fy = [e.pose.y for e in furn]
    fk = [e.kind for e in furn]
    px = [p.pose.x for p in peep]
    py = [p.pose.y for p in peep]

    ax.clear()
    ax.scatter(fx, fy, c="green", marker="s", label="furniture")
    for x, y, k in zip(fx, fy, fk):
        ax.text(x + 0.05, y + 0.05, k)
    ax.scatter(px, py, c="red", marker="o", label="people")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    b = frame.world.get("bounds") if isinstance(frame.world, dict) else None
    if b and isinstance(b, (list, tuple)) and len(b) == 4:
        ax.set_xlim(b[0], b[2])
        ax.set_ylim(b[1], b[3])
    ax.legend()
    ax.grid(True)
    if title:
        ax.set_title(title)

def render_topdown(frame: FrameEvent, show: bool = True, title: Optional[str] = None, ax=None) -> None:
    """Legacy: Render a simple top-down plot. If ax is given, draw on it. Else, create a new figure (legacy)."""
    import matplotlib.pyplot as plt
    if ax is not None:
        draw_floorplan(ax, frame, title)
    else:
        fig, ax1 = plt.subplots(figsize=(6, 4))
        draw_floorplan(ax1, frame, title)
        if show:
            plt.show()
