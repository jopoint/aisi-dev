import tempfile
import json
from pathlib import Path
from src.aisi_sensing.apps.compare_sessions import compare_summaries

def test_compare_summaries_counts_and_transitions():
    # Create two synthetic summaries
    a = {
        "frames": [
            {"frame_id": 0, "layout": "A", "social": "X"},
            {"frame_id": 1, "layout": "B", "social": "Y"},
            {"frame_id": 2, "layout": "A", "social": "Y"},
        ]
    }
    b = {
        "frames": [
            {"frame_id": 0, "layout": "A", "social": "X"},
            {"frame_id": 1, "layout": "A", "social": "Y"},
            {"frame_id": 2, "layout": "B", "social": "Y"},
        ]
    }
    cmp = compare_summaries(a, b)
    # Check label counts
    assert cmp["label_counts"]["a"]["layout"] == {"A": 2, "B": 1}
    assert cmp["label_counts"]["b"]["layout"] == {"A": 2, "B": 1}
    # Check transitions
    assert cmp["transitions"]["a"]["layout"] == {"A->B": 1, "B->A": 1}
    assert cmp["transitions"]["b"]["layout"] == {"A->A": 1, "A->B": 1}
    # Check disagreements
    assert len(cmp["disagreements"]) == 2
    assert cmp["disagreements"][0]["frame_id"] == 1
    assert cmp["disagreements"][1]["frame_id"] == 2
