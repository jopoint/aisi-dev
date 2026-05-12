from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
from collections import Counter, defaultdict

def load_or_export_summary(session_or_json: Path) -> dict:
    if session_or_json.is_dir():
        summary_path = session_or_json / "summary.json"
        events_path = session_or_json / "events.jsonl"
        if not summary_path.exists():
            # Run replay to export summary
            cmd = [
                "python", "-m", "aisi_sensing.apps.run_replay",
                "--events", str(session_or_json),
                "--no-gui", "--export", str(summary_path)
            ]
            print(f"Exporting summary for {session_or_json}...")
            subprocess.run(cmd, check=True)
        with open(summary_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        with open(session_or_json, "r", encoding="utf-8") as f:
            return json.load(f)

def compute_transitions(labels):
    transitions = Counter()
    for prev, curr in zip(labels, labels[1:]):
        transitions[f"{prev}->{curr}"] += 1
    return dict(transitions)

def compare_summaries(a: dict, b: dict) -> dict:
    result = {}
    # Label counts
    a_layouts = [f["layout"] for f in a["frames"]]
    b_layouts = [f["layout"] for f in b["frames"]]
    a_socials = [f["social"] for f in a["frames"]]
    b_socials = [f["social"] for f in b["frames"]]
    result["label_counts"] = {
        "a": {"layout": dict(Counter(a_layouts)), "social": dict(Counter(a_socials))},
        "b": {"layout": dict(Counter(b_layouts)), "social": dict(Counter(b_socials))},
    }
    # Transitions
    result["transitions"] = {
        "a": {
            "layout": compute_transitions(a_layouts),
            "social": compute_transitions(a_socials),
        },
        "b": {
            "layout": compute_transitions(b_layouts),
            "social": compute_transitions(b_socials),
        },
    }
    # Frame-level disagreements
    a_frames = {f["frame_id"]: f for f in a["frames"]}
    b_frames = {f["frame_id"]: f for f in b["frames"]}
    common_ids = sorted(set(a_frames) & set(b_frames))
    disagreements = []
    for fid in common_ids:
        af, bf = a_frames[fid], b_frames[fid]
        if af["layout"] != bf["layout"] or af["social"] != bf["social"]:
            disagreements.append({
                "frame_id": fid,
                "a": {"layout": af["layout"], "social": af["social"]},
                "b": {"layout": bf["layout"], "social": bf["social"]},
            })
            if len(disagreements) >= 20:
                break
    result["disagreements"] = disagreements
    return result

def print_report(a_path, b_path, cmp):
    print(f"=== Session A: {a_path}")
    print(f"=== Session B: {b_path}\n")
    print("Label counts:")
    for lbl in ("layout", "social"):
        print(f"  {lbl.title()}:")
        print(f"    A: {cmp['label_counts']['a'][lbl]}")
        print(f"    B: {cmp['label_counts']['b'][lbl]}")
    print("\nTop transitions:")
    for lbl in ("layout", "social"):
        print(f"  {lbl.title()} transitions:")
        print(f"    A: {cmp['transitions']['a'][lbl]}")
        print(f"    B: {cmp['transitions']['b'][lbl]}")
    print("\nFrame-level disagreements (first 20):")
    for d in cmp["disagreements"]:
        print(f"  Frame {d['frame_id']}: A=({d['a']['layout']}, {d['a']['social']}) B=({d['b']['layout']}, {d['b']['social']})")
    if not cmp["disagreements"]:
        print("  None")

def main():
    parser = argparse.ArgumentParser(description="Compare two replay session summaries.")
    parser.add_argument("--a", required=True, help="Session folder or summary.json for A")
    parser.add_argument("--b", required=True, help="Session folder or summary.json for B")
    parser.add_argument("--out", type=str, default=None, help="Write comparison JSON here")
    args = parser.parse_args()
    a_path = Path(args.a)
    b_path = Path(args.b)
    a_sum = load_or_export_summary(a_path)
    b_sum = load_or_export_summary(b_path)
    cmp = compare_summaries(a_sum, b_sum)
    print_report(a_path, b_path, cmp)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(cmp, f, indent=2)
        print(f"Comparison written to {args.out}")

if __name__ == "__main__":
    main()
