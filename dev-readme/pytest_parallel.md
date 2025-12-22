
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
