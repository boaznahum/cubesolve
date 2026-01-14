# PowerShell Configuration

## Custom Prompt Setup

This document describes the custom PowerShell prompt configuration for this project.

### Features

The custom prompt displays:
- **Virtual Environment**: Shows the active Python virtual environment name in green
- **Current Directory**: Shows the current working directory in cyan
- **Git Branch**: Shows the current git branch name in yellow

### Example

When you're in a virtual environment and on a git branch, the prompt looks like:
```
(.venv314) F:\Dev\code\python\cubesolve [p314]>
```

### Profile Location

The PowerShell profile is located at:
```
C:\Users\boaz2\OneDrive\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
```

### How It Works

The profile contains a custom `prompt` function that:

1. **Detects Virtual Environment**: Checks `$env:VIRTUAL_ENV` to see if a virtual environment is active
2. **Gets Git Branch**: Uses `git rev-parse --abbrev-ref HEAD` to get the current branch name
3. **Formats Output**: Combines the information with color coding using `Write-Host`

### Reloading the Profile

After making changes to the profile, reload it with:
```powershell
. $PROFILE
```

Or simply restart your PowerShell session.

### Customization

You can customize the colors by editing the profile and changing the `-ForegroundColor` values:
- Available colors: Black, DarkBlue, DarkGreen, DarkCyan, DarkRed, DarkMagenta, DarkYellow, Gray, DarkGray, Blue, Green, Cyan, Red, Magenta, Yellow, White

Example:
```powershell
Write-Host $venvPrompt -NoNewline -ForegroundColor Magenta  # Change venv color to magenta
```

### Troubleshooting

If the prompt doesn't appear:
1. Check that the profile exists: `Test-Path $PROFILE`
2. Check for errors in the profile: `. $PROFILE` and look for error messages
3. Verify git is in your PATH: `Get-Command git`
4. Make sure you're using PowerShell 7 (pwsh), not Windows PowerShell (powershell)
