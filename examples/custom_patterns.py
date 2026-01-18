"""
Example custom patterns file.

Copy to ~/.claude/permissions/custom.py for global use,
or to .claude/permissions/custom.py for project-specific patterns.
"""

# Additional wrapper prefixes to strip before checking core command
WRAPPER_PATTERNS = [
    # (r"^sudo\s+", "sudo"),  # Uncomment if you trust sudo
]

# Additional safe commands (checked after wrappers stripped)
SAFE_COMMANDS = [
    # Container tools (read-only)
    # (r"^docker\s+(ps|images|logs|inspect)\b", "docker read"),
    # (r"^kubectl\s+(get|describe|logs)\b", "kubectl read"),

    # Your project's CLI tools
    # (r"^my-cli\b", "my-cli"),
]
