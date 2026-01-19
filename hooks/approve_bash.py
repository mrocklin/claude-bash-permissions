#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Compositional Bash Command Approval

Approves bash commands by decomposing them into WRAPPERS + CORE COMMAND.
"""
from __future__ import annotations
import json
import os
import sys
import re
from pathlib import Path
from typing import Any, Optional

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


def ask_with_hint(cmd_key: str, is_new: bool) -> None:
    """Output 'ask' decision with context to prompt Claude about adding pattern."""
    hint = f"Unknown command '{cmd_key}'"

    hook_output: dict[str, Any] = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": hint
    }

    # Add context prompting Claude to offer adding the pattern
    if is_new:
        data_dir = get_data_dir()
        hook_output["additionalContext"] = (
            f"The command '{cmd_key}' is not in your safe patterns. "
            f"Plugin data directory: {data_dir} "
            f"After this command runs, ask the user: \"Would you like me to add '{cmd_key}' "
            f"to your safe command patterns so it auto-approves next time?\""
        )

    output = {"hookSpecificOutput": hook_output}

    print(json.dumps(output))
    sys.exit(0)


# Commands that have subcommands - track "cmd subcommand" not just "cmd"
SUBCOMMAND_TOOLS = {"git", "docker", "kubectl", "npm", "yarn", "cargo", "go", "pip", "uv", "brew", "apt", "systemctl"}

def get_command_key(core_cmd: str) -> str:
    """Extract the command key for tracking.

    For tools with subcommands (git, docker, etc.), returns "cmd subcommand".
    For other commands, returns just the command name.
    """
    parts = core_cmd.split()
    if not parts:
        return ""
    cmd = parts[0]
    # For subcommand tools, include the subcommand if present
    if cmd in SUBCOMMAND_TOOLS and len(parts) > 1 and not parts[1].startswith("-"):
        return f"{cmd} {parts[1]}"
    return cmd


def get_data_dir() -> Path:
    """Get plugin data directory relative to this script."""
    return Path(__file__).resolve().parent.parent / "data"


def load_seen_commands() -> set:
    """Load set of commands we've seen but not approved."""
    seen_file = get_data_dir() / ".seen"
    if seen_file.exists():
        return set(seen_file.read_text().strip().split("\n"))
    return set()


def save_seen_command(cmd_key: str) -> None:
    """Add command to seen list."""
    seen_file = get_data_dir() / ".seen"
    seen_file.parent.mkdir(parents=True, exist_ok=True)
    seen = load_seen_commands()
    seen.add(cmd_key)
    seen_file.write_text("\n".join(sorted(seen)) + "\n")


def load_never_commands() -> set:
    """Load set of commands user has declined to auto-approve."""
    never_file = get_data_dir() / ".never"
    if never_file.exists():
        return set(never_file.read_text().strip().split("\n"))
    return set()


def split_command_chain(cmd: str):
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

    # Protect escaped semicolons (find -exec \;)
    cmd = cmd.replace(r"\;", "__ESCAPED_SEMI__")

    # Split on command separators
    if quoted_strings:
        segments = re.split(r"\s*(?:&&|\|\||;|\||&)\s*", cmd)
    else:
        segments = re.split(r"\s*(?:&&|\|\||;|\||&)\s*|\n", cmd)

    # Restore protected content
    def restore(s):
        s = re.sub(r"__REDIR_(\d*)_(\d*)__", r"\1>&\2", s)
        s = s.replace("__REDIR_AMPGT__", "&>")
        s = s.replace("__ESCAPED_SEMI__", r"\;")
        for i, qs in enumerate(quoted_strings):
            s = s.replace(f"__QUOTED_{i}__", qs)
        return s

    return [restore(s).strip() for s in segments if s.strip()]


def strip_wrappers(cmd: str, wrapper_patterns: list):
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
    debug = os.environ.get("DEBUG")

    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = data.get("tool_input", {}).get("command", "")

    # Reject command substitution - no hints, just reject
    if re.search(r"\$\(|`", cmd):
        if debug:
            print("REJECTED: command substitution ($() or `) detected", file=sys.stderr)
        sys.exit(0)

    # Load patterns and tracking lists
    wrapper_patterns, safe_commands = load_all_patterns()
    seen_commands = load_seen_commands()
    never_commands = load_never_commands()

    # Process all segments
    segments = split_command_chain(cmd)
    reasons = []

    for segment in segments:
        core_cmd, wrappers = strip_wrappers(segment, wrapper_patterns)
        reason = check_safe(core_cmd, safe_commands)

        if not reason:
            # Command not in safe patterns
            cmd_key = get_command_key(core_cmd)

            if debug:
                if wrappers:
                    print(f"REJECTED: '{segment}' -> core '{core_cmd}' (after stripping {wrappers}) - no matching pattern", file=sys.stderr)
                else:
                    print(f"REJECTED: '{segment}' - no matching pattern", file=sys.stderr)

            # If in never list, silently pass to normal permission flow
            if cmd_key in never_commands:
                sys.exit(0)

            # Check if this is a new command we haven't seen
            is_new = cmd_key not in seen_commands
            if is_new:
                save_seen_command(cmd_key)

            # Ask user with hint about adding pattern
            ask_with_hint(cmd_key, is_new)

        if wrappers:
            reasons.append(f"{'+'.join(wrappers)} + {reason}")
        else:
            reasons.append(reason)

    approve(" | ".join(reasons))


if __name__ == "__main__":
    main()
