
https://www.geeksforgeeks.org/python/run-tests-in-parallel-with-pytest/

```bash
# it is a plugin for pytest
pip install pytest-xdist  

pytest  .\tests\solvers\  -n auto
#plugins: xdist-3.8.0, typeguard-4.4.4
#24 workers [264 items]

# ok too 
pytest -n auto  .\tests\solvers\   
```

add to pyproject.toml
```ini
[tool.pytest.ini_options]

addopts = "-n auto"
```

# Without the plugin
```bash
pip uninstall pytes-xdist
pytest -n auto  .\tests\solvers\

ERROR: usage: python.exe E:\dev\code\cubesolve2\.venv\Scripts\pytest [options] [file_or_dir] [file_or_dir] [...]
python.exe E:\dev\code\cubesolve2\.venv\Scripts\pytest: error: unrecognized arguments: -n
  inifile: E:\dev\code\cubesolve\pyproject.toml
  rootdir: E:\dev\code\cubesolve

 
```

The same error you get when trying to add to pyproject.toml

# Viewing Full Test Failure Output in PyCharm

When tests fail with long assertion messages (e.g., failure tables), PyCharm may truncate the output. Here's how to see the full message:

## Option 1: Click on the failed test
- In the "Run" panel, click on the failed test name
- The full assertion message (including tables) shows in the right panel

## Option 2: Add pytest flags
- Go to: Run → Edit Configurations → your pytest config
- Add to "Additional Arguments": `-s --tb=short`
  - `-s` shows print output (disables capture)
  - `--tb=short` reduces traceback noise

## Option 3: "Click to see difference"
- PyCharm shows a link "Click to see difference" for failed assertions
- Click it to see the full assertion message in a popup

## Option 4: Scroll in output
- Simply scroll up in the Run panel output area
- The full pytest output including tables appears above the traceback

## Option 5: Double-click failed test
- Double-click on the failed test in the test tree
- This often expands to show the full assertion message
