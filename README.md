# claude-bash-permissions

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
/plugin marketplace add mrocklin/claude-bash-permissions
/plugin install claude-bash-permissions@mrocklin-plugins
```

**Option 2: Manual install**
```bash
git clone https://github.com/mrocklin/claude-bash-permissions ~/.claude/plugins/claude-bash-permissions
```
Then add to `~/.claude/settings.json`:
```json
{
  "plugins": ["~/.claude/plugins/claude-bash-permissions"]
}
```

Restart Claude Code. Verify with `/hooks`.

## Customization

**Easy way:** Just ask Claude - "approve docker commands" or "add myctl to safe commands". The plugin includes a skill that helps Claude add patterns for you.

**Manual way:** Edit `{plugin}/data/patterns.py` - all patterns are in one editable file.

Or add project-specific patterns in `.claude/permissions/*.py`.

Restart Claude Code after changes.

## Data Storage

All plugin data is stored in `{plugin}/data/`:
- `patterns.py` - All safe command patterns (editable)
- `.seen` - Commands encountered (for suggestions)
- `.never` - Commands declined for auto-approval

## Security

**Rejected automatically:**
- Command substitution: `$(...)` and backticks
- Any command not matching a safe pattern

**You decide:**
- What wrappers to trust
- What commands are safe for your workflow
