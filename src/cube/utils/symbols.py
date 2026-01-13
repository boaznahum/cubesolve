"""
Terminal symbols with ANSI styling.

Usage:
    from cube.utils.symbols import green_line
    print(green_line(40))  # ════════════════════════════════════════
"""

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

# Unicode box drawing characters
DOUBLE_HORIZONTAL = "═"  # U+2550 ═══════════
SINGLE_HORIZONTAL = "─"  # U+2500 ───────────
HEAVY_HORIZONTAL = "━"   # U+2501 ━━━━━━━━━━━


def styled(text: str, *styles: str) -> str:
    """Wrap text with ANSI styles and reset at end."""
    return "".join(styles) + text + RESET


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions for styled lines
# ══════════════════════════════════════════════════════════════════════════════

def green_line(n: int = 40) -> str:
    """Bold green double line: ════════════════════"""
    return styled(DOUBLE_HORIZONTAL * n, BOLD, GREEN)
