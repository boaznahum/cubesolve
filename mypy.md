python -m pip install -e .[dev]

mypy -p cube

 Yes, pyproject.toml replaces mypy.ini. Let me consolidate them and make pyproject.toml the single source of truth:


 run the mypy configuration


