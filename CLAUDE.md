# Claude Permissions Plugin

A Claude Code plugin for compositional bash command approval using regex patterns.

## Problem

Claude Code's built-in permissions use prefix matching which is too rigid:
- `Bash(git diff:*)` matches `git diff --staged` but NOT `git -C /path diff`
- `Bash(timeout 30 pytest:*)` matches only that exact timeout

This causes constant permission prompts for safe command variations.

## Solution

Decompose commands into **wrappers + core command**:

```
timeout 60 RUST_BACKTRACE=1 cargo test
   │          │                │
   └──────────┴── wrappers ────┴── safe_command(cargo)
```

Chained commands (`&&`, `|`, `;`) are split and each segment validated independently.

## Architecture

```
claude-permissions/
├── .claude-plugin/plugin.json   # Plugin metadata
├── hooks/
│   ├── hooks.json               # Hook registration (PreToolUse on Bash)
│   └── approve_bash.py          # Hook implementation
├── patterns/
│   ├── __init__.py              # Pattern loading, merges all sources
│   └── base.py                  # Default WRAPPER_PATTERNS + SAFE_COMMANDS
├── skills/
│   └── add-pattern/SKILL.md     # Skill for adding new patterns
├── examples/
│   └── custom_patterns.py       # Template for user customization
```

### Pattern Loading Order

`patterns/__init__.py` merges patterns from:
1. `patterns/base.py` - Plugin defaults
2. `~/.claude/permissions/*.py` - User's global customizations
3. `.claude/permissions/*.py` - Project-specific patterns

### Hook Logic (approve_bash.py)

1. Reject if command contains `$(...)` or backticks (command substitution)
2. Split command on `&&`, `||`, `;`, `|`, `&` into segments
3. For each segment:
   - Strip wrapper prefixes iteratively (timeout, env vars, .venv/bin/, etc.)
   - Check if remaining core matches a SAFE_COMMANDS pattern
4. If ALL segments safe → approve with reason; else → reject (no output)

## Pattern Format

Both lists are `[(regex, name), ...]`:

```python
WRAPPER_PATTERNS = [
    (r"^timeout\s+\d+\s+", "timeout"),
    (r"^([A-Z_][A-Z0-9_]*=[^\s]*\s+)+", "env vars"),
]

SAFE_COMMANDS = [
    (r"^git\s+(-C\s+\S+\s+)?(diff|log|status)\b", "git read"),
    (r"^cargo\s+(build|test|run)\b", "cargo"),
]
```

## Testing

```bash
# Should approve
echo '{"tool_name": "Bash", "tool_input": {"command": "timeout 30 cargo test"}}' | python3 hooks/approve_bash.py

# Should reject (no output)
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | python3 hooks/approve_bash.py
```

## TODO

- Submit to official plugin directory once stable
