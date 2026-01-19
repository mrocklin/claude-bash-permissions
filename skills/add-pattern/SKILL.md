---
description: Add or decline safe command patterns for claude-permissions
---

# Add Pattern Skill

When the user wants to approve a new command pattern (e.g., "approve foo commands", "add docker to safe commands"), or when you see a hint about an unknown command, help manage their patterns.

## Data Files

Find the plugin data directory:
```bash
find ~/.claude/plugins/cache -name "patterns.py" -path "*claude-bash-permissions*" | head -1 | xargs dirname
```

Files in that directory:
- `patterns.py` - All safe command patterns (edit this)
- `.seen` - Commands we've encountered but not decided on
- `.never` - Commands user has declined to auto-approve

## When to Use

1. User explicitly asks to approve a command
2. You see a permission prompt with "Unknown command 'X' - consider adding to safe patterns"
3. User declines to add a pattern (add to .never list)

## Adding a Pattern

1. First, check what commands have been seen but not approved:
   ```bash
   cat $(find ~/.claude/plugins/cache -name ".seen" -path "*claude-bash-permissions*" | head -1)
   ```

2. Ask clarifying questions if needed:
   - What command/tool? (e.g., `foo`, `docker`, `myctl`)
   - Read-only or write operations? (affects pattern specificity)
   - Any subcommands to restrict? (e.g., `docker ps` vs all docker)

3. Generate the pattern tuple:
   ```python
   (r"^foo\b", "foo"),  # Simple: any foo command
   (r"^foo\s+(list|show|get)\b", "foo read"),  # Restricted to read ops
   ```

4. Add to patterns.py (append to SAFE_COMMANDS list)

5. Remove from `.seen` if present

6. Tell user to restart Claude Code for changes to take effect.

## Declining a Pattern

If user says "no, don't auto-approve X" or "X should always ask":

1. Add command to `{plugin}/data/.never` (one command per line)
2. Remove from `data/.seen` if present
3. Future uses of that command will go straight to permission prompt without hints

## Pattern file template

```python
"""Custom safe command patterns."""

WRAPPER_PATTERNS = []

SAFE_COMMANDS = [
    # Add patterns here
]
```

## Example: Adding

User: "approve docker commands"

Response: Add to {plugin}/data/patterns.py:
```python
SAFE_COMMANDS = [
    (r"^docker\b", "docker"),
]
```

## Example: Declining

User: "no, git commit should always ask"

Response: Add "git" to {plugin}/data/.never
