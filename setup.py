"""
Ableton Bounce Automator — cx_Freeze build script
==================================================
Requirements:
    pip install cx_freeze pywin32 pyautogui Pillow

Build:
    python setup.py build

Output: build/exe.win-amd64-3.xx/AbletonBounceAutomator.exe
"""

import sys
import os
from pathlib import Path
from cx_Freeze import setup, Executable

# ── pywin32 DLLs (required — cx_Freeze does not auto-detect them) ────────────
import sysconfig
_py_ver   = f"{sys.version_info.major}{sys.version_info.minor}"
_site_pkg = Path(sysconfig.get_path("platlib"))
_win32sys = _py_ver  # pywintypes314.dll etc.

_pywin32_dlls = []
for dll_name in [f"pywintypes{_py_ver}.dll", f"pythoncom{_py_ver}.dll"]:
    for candidate in [
        _site_pkg / "pywin32_system32" / dll_name,
        _site_pkg / "win32" / dll_name,
        Path(sys.prefix) / dll_name,
    ]:
        if candidate.exists():
            _pywin32_dlls.append((str(candidate), dll_name))
            break

# ── Build options ─────────────────────────────────────────────────────────────
build_exe_options = {
    "packages": [
        "tkinter",
        "win32gui",
        "win32con",
        "win32api",
        "pywintypes",
        "pyautogui",
        "pyscreeze",
        "PIL",
        "xml.etree.ElementTree",
        "gzip",
        "threading",
        "socket",
        "json",
        "winreg",
        "hmac",
        "hashlib",
        "subprocess",
        "pathlib",
        "datetime",
    ],
    "excludes": [
        "unittest",
        "test",
        "email",
        "html",
        "http",
        "urllib",
        "xmlrpc",
        "pydoc",
        "doctest",
        "difflib",
        "ftplib",
        "calendar",
    ],
    "include_files": _pywin32_dlls,
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
    "silent": True,
}

# ── Executable ────────────────────────────────────────────────────────────────
icon_path = "icon.ico"  # place an icon.ico here to embed it (optional)

executables = [
    Executable(
        script        = "ableton_bouncer.py",
        base          = "Win32GUI",          # no console window
        target_name   = "AbletonBounceAutomator.exe",
        icon          = icon_path if os.path.exists(icon_path) else None,
        copyright     = "© Robledo Silva",
        shortcut_name = "Ableton Bounce Automator",
        shortcut_dir  = "DesktopFolder",
    )
]

# ── Setup ─────────────────────────────────────────────────────────────────────
setup(
    name        = "Ableton Bounce Automator",
    version     = "2.0",
    description = "Batch MP3 exporter for Ableton Live projects",
    author      = "Robledo Silva",
    options     = {"build_exe": build_exe_options},
    executables = executables,
)
