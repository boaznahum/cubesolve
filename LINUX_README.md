# Linux / WSL Setup Guide

This guide explains how to set up the Rubik's Cube application on Linux or Windows Subsystem for Linux (WSL).

## System Requirements

### Operating System
- **Linux**: Ubuntu 20.04+ (or equivalent)
- **WSL**: WSL2 with Ubuntu 24.04 (recommended)

Check your system:
```bash
uname -a
# Example output: Linux BoazWin11Office 6.6.87.2-microsoft-standard-WSL2 ...
```

Check WSL version (from Windows PowerShell):
```powershell
wsl --list --verbose
# Should show VERSION 2
```

### Python Version
- **Required**: Python 3.10 or later
- **Recommended**: Python 3.14

Check your Python version:
```bash
python3 --version
# Should show: Python 3.14.0 or later
```

## Required System Libraries

The GUI application requires OpenGL libraries. These are **system libraries** (not Python packages) and must be installed using your package manager.

### Check What's Already Installed

```bash
# Check for OpenGL libraries
ldconfig -p | grep -E "(libGL|libGLU)"

# Check installed Mesa packages
dpkg -l | grep -E "(libglu|mesa)" | grep -v "^rc"
```

### Install Missing Libraries

If `libGLU` is missing (common on WSL), install it:

```bash
# Update package list
sudo apt-get update

# Install OpenGL Utility library (if not already installed)
sudo apt-get install -y libglu1-mesa

# Optional: Install GL development libraries (only needed for compiling)
sudo apt-get install -y libgl1-mesa-dev

# Note: libgl1-mesa-glx is deprecated in Ubuntu 24.04+
# It's been replaced by libgl1 which is usually pre-installed
```

### Verify Installation

After installation, verify the libraries are present:

```bash
ldconfig -p | grep GLU
# Should show: libGLU.so.1 => /lib/x86_64-linux-gnu/libGLU.so.1
```

Check package version:
```bash
dpkg -l | grep libglu1-mesa
# Example output:
# ii  libglu1-mesa:amd64  9.0.1-1build1  amd64  Mesa OpenGL utility library
```

## Python Dependencies

Install Python packages from requirements file:

```bash
# Activate your virtual environment first
source .venv314/bin/activate  # Linux/WSL
# or
.venv314\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt
```

Check installed Python packages:
```bash
pip list | grep -E "(pyglet|numpy)"
# Should show:
# pyglet  1.5.31
# numpy   2.3.5
```

## Display Requirements for GUI

### WSL Specific Setup

WSL doesn't have a display server by default. You have two options:

#### Option 1: WSLg (Windows 11 only, recommended)
Windows 11 includes WSLg (WSL GUI) which provides automatic X11 forwarding.

Check if WSLg is available:
```bash
echo $DISPLAY
# Should show something like: :0 or :1
```

If empty, you may need to update WSL:
```powershell
# From Windows PowerShell (as Administrator)
wsl --update
wsl --shutdown
# Then restart WSL
```

#### Option 2: X11 Server (Windows 10 or if WSLg doesn't work)
1. Install an X11 server on Windows:
   - [VcXsrv](https://sourceforge.net/projects/vcxsrv/) (free)
   - [Xming](http://www.straightrunning.com/XmingNotes/) (free)

2. Start the X11 server with "Disable access control" option

3. Set DISPLAY variable in WSL:
```bash
# Add to ~/.bashrc
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0

# Reload
source ~/.bashrc
```

4. Test X11 connection:
```bash
# Install x11-apps if needed
sudo apt-get install x11-apps

# Test
xclock  # Should show a clock window
```

### Native Linux
On native Linux, ensure you have a display server running (X11 or Wayland). This is typically already configured.

## Running the Application

### GUI Application (requires display)
```bash
python3 main_g.py
```

If you see an error like:
```
ImportError: Library "GLU" not found.
```
You need to install libglu1-mesa (see above).

### Console Application (headless, no GUI needed)
```bash
python3 main_c.py
```

### Tests (headless, no GUI needed)
```bash
# Run all tests
python3 -c "import sys; sys.path.insert(0, '.'); from cube.tests.test_all import main; main()"

# Or run individual test files
python3 cube/tests/test_boy.py
python3 cube/tests/test_cube.py
```

Tests explicitly disable animation and don't require OpenGL/GUI libraries.

## Performance Considerations

### GPU Acceleration in WSL

**Important**: WSL2 uses software rendering by default, which is significantly slower than native Windows.

Check your OpenGL renderer:
```bash
python3 -c "
import pyglet
import pyglet.gl as gl
import ctypes

window = pyglet.window.Window(visible=False)
renderer = gl.glGetString(gl.GL_RENDERER)
print('GL Renderer:', ctypes.string_at(renderer).decode())
window.close()
"
```

If you see **"llvmpipe"** - you're using CPU software rendering (slow).
If you see your GPU name (e.g., "NVIDIA", "AMD", "Intel") - you're using hardware acceleration (fast).

### Enabling GPU Acceleration in WSL (Windows 11 only)

WSL2 can use your Windows GPU with these steps:

1. **Update to latest WSL**:
```powershell
# From Windows PowerShell (as Administrator)
wsl --update
wsl --shutdown
```

2. **Ensure you have Windows 11** with the latest updates

3. **Install GPU drivers** (if not already installed):
   - NVIDIA: Download latest driver from nvidia.com
   - AMD: Download latest driver from amd.com
   - Intel: Usually included in Windows updates

4. **Verify GPU passthrough**:
```bash
# In WSL
nvidia-smi  # For NVIDIA GPUs
# Should show your GPU name and driver version
```

5. **Install mesa-utils for diagnostics**:
```bash
sudo apt-get install -y mesa-utils
glxinfo | grep "OpenGL renderer"
# If still showing "llvmpipe", continue to next step
```

6. **Force use of NVIDIA GPU** (if nvidia-smi works but pyglet still uses llvmpipe):

The issue is that WSLg defaults to Mesa software rendering. To use NVIDIA:

```bash
# Method 1: Use __NV_PRIME_RENDER_OFFLOAD
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
python3 main_g.py

# Method 2: Set in your shell profile
echo 'export __NV_PRIME_RENDER_OFFLOAD=1' >> ~/.bashrc
echo 'export __GLX_VENDOR_LIBRARY_NAME=nvidia' >> ~/.bashrc
source ~/.bashrc
```

After setting these environment variables, re-check the renderer:
```bash
python3 -c "
import pyglet, pyglet.gl as gl, ctypes
w = pyglet.window.Window(visible=False)
print('Renderer:', ctypes.string_at(gl.glGetString(gl.GL_RENDERER)).decode())
w.close()
"
```

If you see "NVIDIA" in the renderer name, hardware acceleration is working!

### Performance Comparison

- **Windows (hardware)**: 60 FPS, smooth rotation
- **WSL + llvmpipe (software)**: 5-15 FPS, choppy rendering
- **WSL + GPU passthrough (hardware)**: Similar to Windows

If GPU acceleration doesn't work or isn't available:
- **Recommended**: Run the GUI application directly on Windows (not in WSL)
- **Alternative**: Use the console version (`main_c.py`) for development/testing
- **Tests**: Run in WSL (they don't need GUI)

## Troubleshooting

### Error: "ImportError: Library 'GLU' not found"
**Cause**: Missing libGLU system library
**Solution**: Install libglu1-mesa (see Installation section above)

### Error: "ModuleNotFoundError: No module named 'cube'"
**Cause**: Running from wrong directory or Python path not set
**Solution**:
- Run from project root directory
- Or add to PYTHONPATH: `export PYTHONPATH=/home/boaz/dev/cubesolve`

### Error: "cannot open display"
**Cause**: No X11 server available (WSL issue)
**Solution**:
- Set up WSLg or X11 server (see Display Requirements section)
- For tests: They should run without display
- For GUI app: You need a display server

### PyCharm Run Configurations Fail
**Cause**: Working directory set to subdirectory instead of project root
**Solution**:
- In PyCharm: Run → Edit Configurations
- Set "Working directory" to project root (not `cube/tests`)
- This has been fixed in recent commits

## Version Information

Check all version requirements:

```bash
# System info
uname -a
lsb_release -a  # Linux distribution

# Python
python3 --version

# Python packages
pip list

# System libraries
dpkg -l | grep -E "(libglu|mesa)"
ldconfig -p | grep -E "(libGL|libGLU)"

# Display (for GUI)
echo $DISPLAY
echo $WAYLAND_DISPLAY
```

## Development Notes

### Why Tests Don't Need GUI
All test files explicitly pass `animation=False` when creating apps:
```python
app = AbstractApp.create_non_default(n, animation=False)
```

This ensures tests can run in headless environments (CI/CD, servers, WSL without X11).

### Why GUI Requires OpenGL
The visualization uses pyglet, which is an OpenGL-based graphics library. On Linux, this requires:
- **libGL.so**: OpenGL library (usually pre-installed)
- **libGLU.so**: OpenGL Utility library (must be installed manually)

These are standard Linux graphics stack components, not Python-specific.

## Getting Help

If you encounter issues not covered here:
1. Check the error message for specific library names
2. Search for the library in Ubuntu packages: `apt-cache search <library-name>`
3. Check pyglet documentation: https://pyglet.readthedocs.io/
4. For WSL-specific issues: https://docs.microsoft.com/windows/wsl/
