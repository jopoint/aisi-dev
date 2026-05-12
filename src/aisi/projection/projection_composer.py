from __future__ import annotations

from aisi.core.models import (
    LayoutProposal,
    Point2D,
    ProjectionChairItem,
    ProjectionPayload,
    ProjectionTableItem,
    SceneState,
)


def compose_projection_payload(
    scene_state: SceneState,
    layout_proposal: LayoutProposal,
    fade_out_seconds: float = 120.0,
    show_chairs: bool = False,
) -> ProjectionPayload:
    """Compose projection payload from source scene and target layout."""
    source_tables = {table.table_id: table for table in scene_state.tables}
    source_chairs = {chair.chair_id: chair for chair in scene_state.chairs}

    table_items: list[ProjectionTableItem] = []
    for target in layout_proposal.table_targets:
        source = source_tables.get(target.table_id)
        if source is None:
            continue
        table_items.append(
            ProjectionTableItem(
                table_id=target.table_id,
                source=Point2D(source.x, source.y),
                target=Point2D(target.target_x, target.target_y),
                source_rot_deg=source.rot_deg,
                target_rot_deg=target.target_rot_deg,
            )
        )

    chair_items: list[ProjectionChairItem] = []
    if show_chairs:
        for target in layout_proposal.chair_targets:
            source = source_chairs.get(target.chair_id)
            if source is None:
                continue
            chair_items.append(
                ProjectionChairItem(
                    chair_id=target.chair_id,
                    source=Point2D(source.x, source.y),
                    target=Point2D(target.target_x, target.target_y),
                )
            )

    return ProjectionPayload(
        fade_out_seconds=fade_out_seconds,
        show_chairs=show_chairs,
        tables=table_items,
        chairs=chair_items,
        metadata={
            "learning_format": scene_state.learning_format,
            "table_item_count": len(table_items),
            "chair_item_count": len(chair_items),
        },
    )
