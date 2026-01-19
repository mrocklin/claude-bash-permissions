"""
Pattern loading.

Loads patterns from:
1. {plugin}/data/*.py (user patterns, editable)
2. .claude/permissions/*.py (project-specific, uses CLAUDE_PROJECT_DIR)
"""
import importlib.util
import os
from pathlib import Path


def get_data_dir() -> Path:
    """Get plugin data directory."""
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        return Path(plugin_root) / "data"
    return Path(__file__).parent.parent / "data"


def load_patterns_from_file(path: Path) -> tuple[list, list]:
    """Load WRAPPER_PATTERNS and SAFE_COMMANDS from a .py file."""
    spec = importlib.util.spec_from_file_location("patterns", path)
    if not spec or not spec.loader:
        return [], []
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return [], []
    return (
        getattr(module, "WRAPPER_PATTERNS", []),
        getattr(module, "SAFE_COMMANDS", []),
    )


def load_all_patterns() -> tuple[list, list]:
    """Load patterns from data dir + project dir."""
    wrappers = []
    commands = []

    # User patterns: {plugin}/data/*.py
    data_dir = get_data_dir()
    if data_dir.exists():
        for f in sorted(data_dir.glob("*.py")):
            w, c = load_patterns_from_file(f)
            wrappers.extend(w)
            commands.extend(c)

    # Project patterns: .claude/permissions/*.py
    project_root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    project_dir = Path(project_root) / ".claude" / "permissions"
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.py")):
            w, c = load_patterns_from_file(f)
            wrappers.extend(w)
            commands.extend(c)

    return wrappers, commands
