---
description: Add a new safe command pattern to claude-permissions
---

# Add Pattern Skill

When the user wants to approve a new command pattern (e.g., "approve foo commands", "add docker to safe commands", "allow myctl"), help them add it to their patterns file.

## Steps

1. Ask clarifying questions if needed:
   - What command/tool? (e.g., `foo`, `docker`, `myctl`)
   - Read-only or write operations? (affects pattern specificity)
   - Any subcommands to restrict? (e.g., `docker ps` vs all docker)

2. Generate the pattern tuple:
   ```python
   (r"^foo\b", "foo"),  # Simple: any foo command
   (r"^foo\s+(list|show|get)\b", "foo read"),  # Restricted to read ops
   ```

3. Add to `~/.claude/permissions/custom.py`:
   - Create file if it doesn't exist
   - Append to SAFE_COMMANDS list
   - Use the template from the plugin's examples/custom_patterns.py

4. Tell user to restart Claude Code for changes to take effect.

## Example interaction

User: "approve docker commands"

Response: Create/update ~/.claude/permissions/custom.py with:
```python
SAFE_COMMANDS = [
    (r"^docker\b", "docker"),
]
```

## Pattern file template

```python
"""Custom safe command patterns."""

WRAPPER_PATTERNS = []

SAFE_COMMANDS = [
    # Add patterns here
]
```
