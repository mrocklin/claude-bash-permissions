"""
Pattern loading and merging.

Loads patterns from:
1. base.py (this plugin's defaults)
2. ~/.claude/permissions/*.py (user customizations)
3. .claude/permissions/*.py (project-specific, uses CLAUDE_PROJECT_DIR)
"""
import importlib.util
import os
from pathlib import Path

from .base import WRAPPER_PATTERNS, SAFE_COMMANDS


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
    """Merge patterns from base + user + project."""
    wrappers = list(WRAPPER_PATTERNS)
    commands = list(SAFE_COMMANDS)

    # User patterns: ~/.claude/permissions/*.py
    user_dir = Path.home() / ".claude" / "permissions"
    if user_dir.exists():
        for f in sorted(user_dir.glob("*.py")):
            w, c = load_patterns_from_file(f)
            wrappers.extend(w)
            commands.extend(c)

    # Project patterns: .claude/permissions/*.py
    # Use CLAUDE_PROJECT_DIR env var if available (set by Claude Code)
    project_root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    project_dir = Path(project_root) / ".claude" / "permissions"
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.py")):
            w, c = load_patterns_from_file(f)
            wrappers.extend(w)
            commands.extend(c)

    return wrappers, commands
