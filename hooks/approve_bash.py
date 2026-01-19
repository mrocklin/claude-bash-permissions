#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Compositional Bash Command Approval

Approves bash commands by decomposing them into WRAPPERS + CORE COMMAND.
Patterns are loaded from:
  - Plugin defaults (patterns/base.py)
  - User customizations (~/.claude/permissions/*.py)
  - Project-specific (.claude/permissions/*.py)

See patterns/base.py for the pattern format.
"""
from __future__ import annotations
import json
import sys
import re
from pathlib import Path
from typing import Optional, List, Tuple

# Add parent to path so we can import patterns
sys.path.insert(0, str(Path(__file__).parent.parent))
from patterns import load_all_patterns


def approve(reason: str) -> None:
    """Output approval JSON and exit."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason
        }
    }))
    sys.exit(0)


def split_command_chain(cmd: str) -> List[str]:
    """Split command into segments on &&, ||, ;, |, &.

    Handles backslash continuations, quoted strings, and redirections.
    """
    # Collapse backslash-newline continuations
    cmd = re.sub(r"\\\n\s*", " ", cmd)

    # Protect quoted strings
    quoted_strings = []
    def save_quoted(m):
        quoted_strings.append(m.group(0))
        return f"__QUOTED_{len(quoted_strings)-1}__"
    cmd = re.sub(r'"[^"]*"', save_quoted, cmd)
    cmd = re.sub(r"'[^']*'", save_quoted, cmd)

    # Protect redirections: 2>&1, &>
    cmd = re.sub(r"(\d*)>&(\d*)", r"__REDIR_\1_\2__", cmd)
    cmd = re.sub(r"&>", "__REDIR_AMPGT__", cmd)

    # Split on command separators
    if quoted_strings:
        segments = re.split(r"\s*(?:&&|\|\||;|\||&)\s*", cmd)
    else:
        segments = re.split(r"\s*(?:&&|\|\||;|\||&)\s*|\n", cmd)

    # Restore protected content
    def restore(s):
        s = re.sub(r"__REDIR_(\d*)_(\d*)__", r"\1>&\2", s)
        s = s.replace("__REDIR_AMPGT__", "&>")
        for i, qs in enumerate(quoted_strings):
            s = s.replace(f"__QUOTED_{i}__", qs)
        return s

    return [restore(s).strip() for s in segments if s.strip()]


def strip_wrappers(cmd: str, wrapper_patterns: list) -> Tuple[str, List[str]]:
    """Strip wrapper prefixes iteratively, return (core_cmd, wrapper_names)."""
    wrappers = []
    changed = True
    while changed:
        changed = False
        for pattern, name in wrapper_patterns:
            m = re.match(pattern, cmd)
            if m:
                wrappers.append(name)
                cmd = cmd[m.end():]
                changed = True
                break
    return cmd.strip(), wrappers


def check_safe(cmd: str, safe_commands: list) -> Optional[str]:
    """Check if command matches a safe pattern. Returns reason or None."""
    for pattern, reason in safe_commands:
        if re.match(pattern, cmd):
            return reason
    return None


def main():
    import os
    debug = os.environ.get("DEBUG")

    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = data.get("tool_input", {}).get("command", "")

    # Reject command substitution
    if re.search(r"\$\(|`", cmd):
        if debug:
            print(f"REJECTED: command substitution ($() or `) detected", file=sys.stderr)
        sys.exit(0)

    # Load patterns
    wrapper_patterns, safe_commands = load_all_patterns()

    # Process all segments
    segments = split_command_chain(cmd)
    reasons = []

    for segment in segments:
        core_cmd, wrappers = strip_wrappers(segment, wrapper_patterns)
        reason = check_safe(core_cmd, safe_commands)

        if not reason:
            if debug:
                if wrappers:
                    print(f"REJECTED: '{segment}' -> core '{core_cmd}' (after stripping {wrappers}) - no matching pattern", file=sys.stderr)
                else:
                    print(f"REJECTED: '{segment}' - no matching pattern", file=sys.stderr)
            sys.exit(0)

        if wrappers:
            reasons.append(f"{'+'.join(wrappers)} + {reason}")
        else:
            reasons.append(reason)

    approve(" | ".join(reasons))


if __name__ == "__main__":
    main()
