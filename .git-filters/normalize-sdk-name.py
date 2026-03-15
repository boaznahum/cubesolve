"""Git clean filter: normalize SDK_NAME in PyCharm run configurations.

Replaces any SDK_NAME value with a canonical placeholder so that
PyCharm's auto-generated SDK_NAME changes don't show up in git diffs.
"""
import re
import sys

# Use binary I/O to preserve line endings (prevents CRLF/LF conversion on Windows)
stdin = sys.stdin.buffer
stdout = sys.stdout.buffer

CANONICAL_SDK_NAME = "uv (cubesolve2)"

for raw_line in stdin:
    line = raw_line.decode("utf-8")
    line = re.sub(
        r'(<option name="SDK_NAME" value=")([^"]*)("\s*/>)',
        rf'\g<1>{CANONICAL_SDK_NAME}\g<3>',
        line,
    )
    stdout.write(line.encode("utf-8"))
