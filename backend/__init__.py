"""
Backend Top-Level Package Initialization.
Ensures the backend directory and workspace root are in sys.path so 'app' and 'database' imports resolve cleanly across environments.
"""

from pathlib import Path
import sys

_backend_dir = str(Path(__file__).parent.resolve())
_root_dir = str(Path(__file__).parent.parent.resolve())

if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

