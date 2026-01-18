"""
Base patterns for compositional command approval.

WRAPPER_PATTERNS: Prefixes that modify HOW a command runs (stripped before checking)
SAFE_COMMANDS: The actual executables considered safe
"""

# =============================================================================
# WRAPPER PATTERNS
# These modify HOW a command runs, stripped before checking core command
# =============================================================================

WRAPPER_PATTERNS = [
    # Execution modifiers
    (r"^timeout\s+\d+\s+", "timeout"),
    (r"^time\s+", "time"),
    (r"^nice\s+(-n\s*\d+\s+)?", "nice"),
    (r"^env\s+", "env"),

    # Environment variables: VAR=value VAR2=value2 command
    (r"^([A-Z_][A-Z0-9_]*=[^\s]*\s+)+", "env vars"),

    # Virtual environment paths
    (r"^(\.\./)*\.?venv/bin/", ".venv"),
    (r"^/[^\s]+/\.?venv/bin/", ".venv"),

    # Shell control flow prefixes
    (r"^do\s+", "do"),
    (r"^then\s+", "then"),
    (r"^else\s+", "else"),

    # Negation and comments
    (r"^!\s*", "!"),
    (r"^#[^\n]*\n\s*", "comment"),
]

# =============================================================================
# SAFE COMMAND PATTERNS
# The actual executables, checked after wrappers are stripped
# =============================================================================

SAFE_COMMANDS = [
    # --- Version Control ---
    (r"^git\s+(-C\s+\S+\s+)?(diff|log|status|show|branch|stash\s+list|bisect|worktree\s+list|fetch|ls-files)\b",
     "git read"),
    (r"^git\s+(-C\s+\S+\s+)?(add|checkout|merge|rebase|stash)\b",
     "git write"),

    # --- Python ---
    (r"^python[23]?\b", "python"),
    (r"^pytest\b", "pytest"),
    (r"^ruff\b", "ruff"),
    (r"^uv\s+(pip|run|sync|venv|add|remove|lock)\b", "uv"),
    (r"^uvx\b", "uvx"),

    # --- JavaScript/Node ---
    (r"^npm\s+(install|run|test|build|ci)\b", "npm"),
    (r"^npx\b", "npx"),

    # --- Rust ---
    (r"^cargo\s+(\+\S+\s+)?(build|test|run|check|clippy|fmt|clean|search|add)\b", "cargo"),
    (r"^rustup\b", "rustup"),
    (r"^maturin\s+(develop|build)\b", "maturin"),

    # --- Build Tools ---
    (r"^make\b", "make"),

    # --- Unix Utilities (read-only / pipeline) ---
    (r"^(ls|cat|head|tail|wc|find|grep|rg|file|which|pwd|du|df|curl|sort|uniq|cut|tr|awk|sed|xargs|tee|open|strings)\b",
     "read-only"),

    # --- File/Directory (low-risk) ---
    (r"^touch\b", "touch"),
    (r"^mkdir\b", "mkdir"),

    # --- Process Management ---
    (r"^(pkill|kill)\b", "process"),
    (r"^(true|false|exit(\s+\d+)?)$", "builtin"),

    # --- Shell Constructs ---
    (r"^echo\b", "echo"),
    (r"^cd\s", "cd"),
    (r"^sleep\s", "sleep"),
    (r"^(source|\.) [^\s]*venv/bin/activate", "venv activate"),
    (r"^[A-Z_][A-Z0-9_]*=\S*$", "var assignment"),

    # --- Control Flow ---
    (r"^for\s+\w+\s+in\s", "for loop"),
    (r"^while\s", "while loop"),
    (r"^if\s", "if"),
    (r"^elif\s", "elif"),
    (r"^do$", "do"),
    (r"^done$", "done"),
    (r"^fi$", "fi"),
]
