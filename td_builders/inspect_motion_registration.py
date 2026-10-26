"""Read-only differences against the registered simulation snapshot.

Never refreshes snapshots, writes parameters, forces cooks, or stops tests.
"""
from collections import Counter
import json


def inspect(resolve):
    from td_builders import motion_output_simulation_test as test
    routing = test.routing
    comp = resolve(routing.PATH)
    if comp is None:
        return {"read_only": True, "error": "Routing fehlt"}
    info = comp.fetch(test.SESSION, None)
    if not isinstance(info, dict):
        return {"read_only": True, "error": "Testregistrierung fehlt"}
    report = {"read_only": True, "snapshots_changed": False,
              "nodes_changed": False, "sections": {}}
    for section in ("expected_protected", "expected_owned"):
        expected = info.get(section, {})
        actual_owned = test.own_snapshot(resolve, comp) if section == "expected_owned" else None
        fields = Counter()
        examples = {}
        changed = 0
        missing = []
        for path, before in expected.items():
            node = resolve(path)
            if node is None:
                missing.append(path)
                continue
            after = actual_owned.get(path) if actual_owned is not None else routing.signature(node)
            if before == after:
                continue
            changed += 1
            after = after or {}
            for field in sorted(set(before) | set(after)):
                old, new = before.get(field), after.get(field)
                if old == new:
                    continue
                pairs = [(field, old, new)]
                if field == "parameters":
                    old, new = old or {}, new or {}
                    pairs = [("parameter:" + key, old.get(key), new.get(key))
                             for key in sorted(set(old) | set(new))
                             if old.get(key) != new.get(key)]
                for key, left, right in pairs:
                    fields[key] += 1
                    if key not in examples:
                        examples[key] = {"path": path,
                            "before": str(left)[:350], "now": str(right)[:350]}
        report["sections"][section] = {"checked": len(expected),
            "changed_nodes": changed, "missing": missing,
            "fields": dict(fields), "examples": examples}
    return report


if __name__ == "__main__":
    print("Im TD-Textport importieren und inspect(op) aufrufen.")
