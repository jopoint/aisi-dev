import argparse, json
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True)
    ap.add_argument("--max-frames", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    seen = defaultdict(set)
    prev = defaultdict(set)
    new_ids = defaultdict(int)
    frames = 0

    with open(args.jsonl, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            frames += 1
            cur = defaultdict(set)

            for o in e.get("furniture", []):
                cur[o["kind"]].add(o["id"])
                seen[o["kind"]].add(o["id"])
            for o in e.get("people", []):
                cur["person"].add(o["id"])
                seen["person"].add(o["id"])

            if frames > 1:
                for k in cur:
                    new_ids[k] += len(cur[k] - prev.get(k, set()))

            prev = cur

            if args.max_frames and frames >= args.max_frames:
                break

    denom = max(frames - 1, 1)
    print("frames", frames)
    print("unique_ids", {k: len(v) for k, v in seen.items()})
    print("new_ids_total", dict(new_ids))
    print("new_ids_per_frame_avg", {k: round(v / denom, 3) for k, v in new_ids.items()})

if __name__ == "__main__":
    main()
