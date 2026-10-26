"""Read canonical geometry in TD Python 3.9 without changing shared modules."""
import ast
from pathlib import Path
import sys
import types


def load_geometry(force_legacy=False):
    if sys.version_info >= (3, 10) and not force_legacy:
        from aisi.core import table_geometry
        return table_geometry
    if sys.version_info < (3, 9):
        raise RuntimeError('Motion-Preview benötigt mindestens Python 3.9; bitte sys.version melden.')
    name = '_aisi_motion_canonical_geometry_py39'
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().parents[1] / 'src/aisi/core/table_geometry.py'
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    # TableState is used only in postponed annotations in this geometry module.
    # Avoid loading the unrelated application model dataclasses in TD 3.9.
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.ImportFrom) and node.module == 'aisi.core.models')]
    # slots only changes instance storage; retain frozen and all geometry code.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Name)
                        and decorator.func.id == 'dataclass'):
                    decorator.keywords = [k for k in decorator.keywords if k.arg != 'slots']
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module  # dataclasses resolves annotation names here.
    try:
        exec(compile(tree, str(path), 'exec'), module.__dict__)
    except Exception:
        del sys.modules[name]
        raise
    return module
