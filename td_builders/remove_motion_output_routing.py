"""Explicit rollback of the owned production content insertion; never saves."""
import builtins
import json
import sys

REPO='C:/dev/Promotion_Prototypen/AISI'


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    if REPO not in sys.path:
        sys.path.insert(0,REPO)
    from td_builders.build_motion_output_routing import uninstall
    print(json.dumps(uninstall(symbol('op')),ensure_ascii=False,indent=2))
