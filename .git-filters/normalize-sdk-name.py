"""Git clean filter: normalize SDK_NAME in PyCharm run configurations.

Replaces any SDK_NAME value with a canonical placeholder so that
PyCharm's auto-generated SDK_NAME changes don't show up in git diffs.
"""
import re
import sys

CANONICAL_SDK_NAME = "uv (cubesolve2)"

for line in sys.stdin:
    line = re.sub(
        r'(<option name="SDK_NAME" value=")([^"]*)("\s*/>)',
        rf'\g<1>{CANONICAL_SDK_NAME}\g<3>',
        line,
    )
    sys.stdout.write(line)
