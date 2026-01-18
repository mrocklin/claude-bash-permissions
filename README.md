# claude-permissions

Compositional Bash command approval for Claude Code. Approves safe command variations without constant permission prompts.

## The Problem

Claude Code's static permissions use prefix matching:
```
"Bash(git diff:*)" matches "git diff --staged" but NOT "git -C /path diff"
"Bash(timeout 30 pytest:*)" matches that exact timeout, not "timeout 20 pytest"
```

## The Solution

Decompose commands into **wrappers + core command**:

```
timeout 60 RUST_BACKTRACE=1 cargo test
   │          │                │
   └──────────┴── wrappers ────┴── safe_command(cargo)
```

Chained commands (`&&`, `|`, etc.) are split and each segment validated.

## Install

**Option 1: From this repo as marketplace**
```bash
/plugin marketplace add mrocklin/claude-permissions
/plugin install claude-permissions@mrocklin-plugins
```

**Option 2: Manual install**
```bash
git clone https://github.com/mrocklin/claude-permissions ~/.claude/plugins/claude-permissions
```
Then add to `~/.claude/settings.json`:
```json
{
  "plugins": ["~/.claude/plugins/claude-permissions"]
}
```

Restart Claude Code. Verify with `/hooks`.

## Customization

**Easy way:** Just ask Claude - "approve docker commands" or "add myctl to safe commands". The plugin includes a skill that helps Claude add patterns for you.

**Manual way:** Add patterns to these locations:

| Location | Scope |
|----------|-------|
| `~/.claude/permissions/*.py` | Your global additions |
| `.claude/permissions/*.py` | Project-specific |

Example `~/.claude/permissions/custom.py`:
```python
WRAPPER_PATTERNS = [
    (r"^sudo\s+", "sudo"),  # If you trust sudo
]

SAFE_COMMANDS = [
    (r"^docker\s+(ps|images|logs)\b", "docker read"),
    (r"^kubectl\s+get\b", "kubectl get"),
    (r"^my-cli\b", "my-cli"),
]
```

Restart Claude Code after changes.

## Test a command

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "YOUR_CMD"}}' | python3 hooks/approve_bash.py
```

## Security

**Rejected automatically:**
- Command substitution: `$(...)` and backticks
- Any command not matching a safe pattern

**You decide:**
- What wrappers to trust
- What commands are safe for your workflow
