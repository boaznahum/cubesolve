"""Git smudge filter: replace canonical SDK_NAME with local machine's SDK name.

Reads the local SDK name from .git-filters/local-sdk-name.txt and replaces
the canonical placeholder with it. This ensures every checkout/branch-switch
gets the correct SDK_NAME for this machine's PyCharm interpreter.
"""
import os
import re
import sys

# Use binary I/O to preserve line endings (prevents CRLF/LF conversion on Windows)
stdin = sys.stdin.buffer
stdout = sys.stdout.buffer

CANONICAL_SDK_NAME = "uv (cubesolve2)"

# Read local SDK name from sibling file
local_sdk_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local-sdk-name.txt")
try:
    with open(local_sdk_file) as f:
        local_sdk_name = f.read().strip()
except FileNotFoundError:
    local_sdk_name = CANONICAL_SDK_NAME  # fallback if file missing

canonical_escaped = re.escape(CANONICAL_SDK_NAME)

for raw_line in stdin:
    line = raw_line.decode("utf-8")
    line = re.sub(
        rf'(<option name="SDK_NAME" value="){canonical_escaped}("\s*/>)',
        rf'\g<1>{local_sdk_name}\g<2>',
        line,
    )
    stdout.write(line.encode("utf-8"))
