"""Attention script using Windows Text-to-Speech.

Speaks through the default audio device (including Bluetooth speakers).
"""
import subprocess
import sys

# Message to speak - customize the name!
NAME = "Friend"
MESSAGE = f"Hey {NAME}! Claude needs your attention!"

try:
    # Use PowerShell's built-in text-to-speech (SAPI)
    # Rate: -2 (slower) to 2 (faster), Volume: 0-100
    ps_script = f'''
    Add-Type -AssemblyName System.Speech
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $synth.Rate = 1
    $synth.Volume = 100
    $synth.Speak("{MESSAGE}")
    '''
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        timeout=10
    )
    print(f"Spoke: {MESSAGE}")
except Exception as e:
    print(f"TTS failed: {e}")
    # Fallback to system sound
    try:
        import winsound
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    except:
        pass
    print(f"ATTENTION: {MESSAGE}")
