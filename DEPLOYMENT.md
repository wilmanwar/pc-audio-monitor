# Deployment Guide - PC Audio Monitor

This guide explains how to distribute and deploy the PC Audio Monitor app.

## Option 1: Direct Python Execution (Easiest)

Share the entire folder with:
1. All `.py` files
2. `requirements.txt`
3. `.env.example` 
4. `run.bat`
5. All documentation files

**Recipient setup**:
```bash
pip install -r requirements.txt
copy .env.example .env
# Edit .env with their Home Assistant details
python main.py
```

## Option 2: PyInstaller Executable (Recommended)

Create a standalone `.exe` that doesn't require Python installed.

### Build Steps

```bash
# Install PyInstaller (already in requirements.txt)
pip install pyinstaller

# Create single executable
pyinstaller --onefile --windowed --add-data ".env.example:." --icon=icon.ico main.py

# The executable will be in: dist\main.exe
```

### Advanced Options

For a more polished executable:

```bash
# With console (for seeing logs)
pyinstaller --onefile --console ^
  --add-data ".env.example:." ^
  --add-data "README.md:." ^
  --add-data "SETUP.md:." ^
  --name "PCMonitor" ^
  --version-file=version.txt ^
  main.py

# Without console (silent operation)
pyinstaller --onefile --windowed ^
  --add-data ".env.example:." ^
  --name "PCMonitor" ^
  main.py
```

### Create Version File

Save as `version.txt`:
```
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx?id=19
VSVersionInfo(
  ffi=FixedFileInfo(
    mask=0x3f,
    mask_values=(0, 0xffff, 0x3f, 0x3f, 0, 0),
    date=(0, 0)
  ),
  StringFileInfo(
    [StringTable(
      '040904B0',
      [StringTableEntry(u'CompanyName', u''),
      StringTableEntry(u'FileDescription', u'PC Audio Monitor for Home Assistant'),
      StringTableEntry(u'FileVersion', u'1.0.0.0'),
      StringTableEntry(u'InternalName', u'PCMonitor'),
      StringTableEntry(u'LegalCopyright', u''),
      StringTableEntry(u'OriginalFilename', u'PCMonitor.exe'),
      StringTableEntry(u'ProductName', u'PC Audio Monitor'),
      StringTableEntry(u'ProductVersion', u'1.0.0.0')])
    ]), 
  VarFileInfo([VarFileEntry(u'Translation', [1033, 1200])])
)
```

Then build:
```bash
pyinstaller --onefile --windowed ^
  --add-data ".env.example:." ^
  --version-file=version.txt ^
  --icon=icon.ico ^
  --name "PCMonitor" ^
  main.py
```

## Option 3: Windows Installer (Advanced)

Use NSIS (Nullsoft Scriptable Install System) to create a professional installer.

### Install NSIS
```bash
winget install NSIS
```

### Create Installer Script

Save as `installer.nsi`:
```nsis
; PC Audio Monitor Installer
; Build with: makensis installer.nsi

!include "MUI2.nsh"
!include "x64.nsh"

Name "PC Audio Monitor"
OutFile "PCMonitor-Setup.exe"
InstallDir "$PROGRAMFILES\PCMonitor"
InstallDirRegKey HKCU "Software\PCMonitor" "InstallDir"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  
  ; Copy executable
  File "dist\PCMonitor.exe"
  
  ; Copy config templates
  File ".env.example"
  File "README.md"
  File "SETUP.md"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\PC Audio Monitor"
  CreateShortCut "$SMPROGRAMS\PC Audio Monitor\PC Monitor.lnk" "$INSTDIR\PCMonitor.exe"
  CreateShortCut "$SMPROGRAMS\PC Audio Monitor\Configuration.lnk" "$INSTDIR\.env.example"
  CreateShortCut "$DESKTOP\PCMonitor.lnk" "$INSTDIR\PCMonitor.exe"
  
  ; Save install path to registry
  WriteRegStr HKCU "Software\PCMonitor" "InstallDir" "$INSTDIR"
SectionEnd
```

Build installer:
```bash
makensis installer.nsi
```

Result: `PCMonitor-Setup.exe` - Professional installer users can run to install the app.

## Distribution Checklist

Before distributing, ensure:

- [ ] `requirements.txt` lists all dependencies
- [ ] `.env.example` has all configuration options documented
- [ ] README.md has quick start instructions
- [ ] SETUP.md has detailed setup steps
- [ ] App runs without errors: `python main.py`
- [ ] `test_ha_integration.py` can be used for troubleshooting
- [ ] Log file location is clearly documented
- [ ] All paths use environment variables or relative paths (not absolute)

## Distribution Methods

### Method 1: GitHub Release
```bash
git init
git add .
git commit -m "Initial PC Audio Monitor release"
git push origin main

# On GitHub: Create Release → Upload dist/main.exe
```

### Method 2: Zip File
```bash
# Create portable zip
Compress-Archive -Path "dist/main.exe", ".env.example", "SETUP.md", "README.md" `
  -DestinationPath "PCMonitor-v1.0.0.zip"
```

### Method 3: Network Share
```bash
# Share entire folder on network
net share PCMonitor=C:\Projects\test-one /grant:Everyone,FULL
```

## Recipient Setup (Standalone Exe)

1. **Download**: `PCMonitor.exe`
2. **Configure**: Create/edit `.env` file in same directory
3. **Run**: Double-click `PCMonitor.exe`

## Troubleshooting Deployments

### Exe won't run / "Missing DLL"
- PyInstaller didn't bundle all dependencies
- Solution: Use `--collect-all sounddevice` flag
- Or: Distribute with Python + pip install approach instead

### Configuration not found
- Ensure `.env` is in the same directory as `.exe`
- Or: Use absolute paths in executable

### Crashes with no error
- Run with console window: `pyinstaller --onefile --console main.py`
- Check `pc_audio_monitor.log` in the app directory

## Maintenance

### Updating Distribution

After making changes:

1. Test locally: `python main.py`
2. Rebuild exe: `pyinstaller --onefile main.py`
3. Test exe: `dist\main.exe`
4. Distribute: Upload new `main.exe`

### Version Tracking

Update version in `.env.example`:
```
# Version: 1.0.0
# Last updated: 2026-04-04
```

And in code:
```python
APP_VERSION = "1.0.0"
```

## Performance Notes

- Standalone `.exe` is ~50-80 MB (includes Python + dependencies)
- Startup time: ~2-3 seconds (Python initialization)
- Memory usage: ~50-80 MB (sounddevice + numpy loaded)
- Disk space: ~100 MB for distribution

---

**Recommended**: Use PyInstaller (Option 2) for most users - it's easy to build and distribute.
