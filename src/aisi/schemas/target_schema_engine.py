from __future__ import annotations

from aisi.core.models import RangePreference, TargetProfile


def get_target_profile(learning_format: str) -> TargetProfile:
    """Return a simple heuristic target profile for a learning format."""
    key = learning_format.lower().strip()

    if key == "input":
        return TargetProfile(
            learning_format="input",
            cluster_count=RangePreference(min_value=1.0, target_value=1.0, max_value=2.0, weight=1.0),
            cluster_compactness=RangePreference(min_value=0.55, target_value=0.75, max_value=0.95, weight=0.9),
            distribution_evenness=RangePreference(min_value=0.35, target_value=0.55, max_value=0.85, weight=0.7),
            frontal_alignment=RangePreference(min_value=0.7, target_value=0.9, max_value=1.0, weight=1.1),
            shared_field_centrality=RangePreference(min_value=0.35, target_value=0.55, max_value=0.75, weight=0.6),
            local_vs_global_focus=RangePreference(min_value=0.55, target_value=0.75, max_value=1.0, weight=0.8),
            target_area_orientation_fit=RangePreference(min_value=0.6, target_value=0.85, max_value=1.0, weight=1.0),
        )

    if key == "groupwork":
        return TargetProfile(
            learning_format="groupwork",
            cluster_count=RangePreference(min_value=2.0, target_value=3.0, max_value=6.0, weight=1.1),
            cluster_compactness=RangePreference(min_value=0.55, target_value=0.8, max_value=1.0, weight=1.0),
            distribution_evenness=RangePreference(min_value=0.45, target_value=0.7, max_value=0.95, weight=1.0),
            frontal_alignment=RangePreference(min_value=0.2, target_value=0.45, max_value=0.75, weight=0.4),
            shared_field_centrality=RangePreference(min_value=0.35, target_value=0.55, max_value=0.8, weight=0.6),
            local_vs_global_focus=RangePreference(min_value=0.45, target_value=0.65, max_value=0.9, weight=0.8),
            target_area_orientation_fit=RangePreference(min_value=0.45, target_value=0.7, max_value=0.95, weight=0.9),
        )

    if key == "discussion":
        return TargetProfile(
            learning_format="discussion",
            cluster_count=RangePreference(min_value=1.0, target_value=1.0, max_value=2.0, weight=0.8),
            cluster_compactness=RangePreference(min_value=0.45, target_value=0.65, max_value=0.9, weight=0.8),
            distribution_evenness=RangePreference(min_value=0.45, target_value=0.75, max_value=1.0, weight=1.0),
            frontal_alignment=RangePreference(min_value=0.15, target_value=0.35, max_value=0.7, weight=0.3),
            shared_field_centrality=RangePreference(min_value=0.7, target_value=0.9, max_value=1.0, weight=1.2),
            local_vs_global_focus=RangePreference(min_value=0.2, target_value=0.4, max_value=0.7, weight=0.9),
            target_area_orientation_fit=RangePreference(min_value=0.45, target_value=0.65, max_value=0.95, weight=0.7),
        )

    allowed = ["input", "groupwork", "discussion"]
    raise ValueError(f"Unknown learning_format '{learning_format}'. Expected one of: {allowed}")
