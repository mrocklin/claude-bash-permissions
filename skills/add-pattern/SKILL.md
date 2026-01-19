---
description: Add or decline safe command patterns for claude-permissions
---

# Add Pattern Skill

When the user wants to approve a new command pattern (e.g., "approve foo commands", "add docker to safe commands"), or when you see a hint about an unknown command, help manage their patterns.

For full context on how the plugin works, read the `CLAUDE.md` and `hooks/approve_bash.py` files in the plugin's root directory (sibling to the data directory).

## Data Files

The data directory is `../../data/` relative to this skill file's directory. Use the "Base directory for this skill" shown above to construct the full path.

**Important:** Edit the file in the `cache` directory, NOT the `marketplaces` directory.

Files in that directory:
- `patterns.py` - All safe command patterns (edit this)
- `.seen` - Commands we've encountered but not decided on
- `.never` - Commands user has declined to auto-approve

## When to Use

1. User explicitly asks to approve a command
2. You see a permission prompt with "Unknown command 'X' - consider adding to safe patterns"
3. User declines to add a pattern (add to .never list)

## Adding a Pattern

1. First, check what commands have been seen but not approved by reading `.seen` in the data directory

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

## Declining a Pattern

If user says "no, don't auto-approve X" or "X should always ask":

1. Add command to `.never` in the data directory (one command per line)
2. Remove from `.seen` if present
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

Response: Add to `patterns.py` in the data directory:
```python
SAFE_COMMANDS = [
    (r"^docker\b", "docker"),
]
```

## Example: Declining

User: "no, git commit should always ask"

Response: Add "git" to `.never` in the data directory
