"""Remove all pip packages except pip itself."""
import subprocess
import sys

# Get all installed packages
result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)

packages = []
for line in result.stdout.strip().split("\n"):
    if not line:
        continue
    if line.startswith("-e"):
        # Editable install: -e git+...#egg=name or -e .
        if "#egg=" in line:
            packages.append(line.split("#egg=")[-1])
    else:
        # Regular: package==version
        packages.append(line.split("==")[0])

# Remove all except pip
for pkg in packages:
    if pkg.lower() != "pip":
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", pkg])
