# PyCharm Silently Fails to Add Interpreter

## Problem

PyCharm silently fails when trying to add/set a Python interpreter.
No error message — it just doesn't work.

## Root Cause

No project structure configured — specifically, no **content root** is set.

## Solution

1. Go to **Settings > Project > Project Structure**
2. Click **Add Content Root** and add your project directory
3. The interpreter should now work

### If You Can't See Project Structure

If PyCharm shows no project structure but you have a `.idea/modules.xml` file:

1. **Delete** `.idea/modules.xml`
2. Restart PyCharm
3. PyCharm will recreate the project structure automatically
4. Then set the interpreter as usual
