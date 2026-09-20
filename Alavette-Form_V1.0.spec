# -*- mode: python ; coding: utf-8 -*-
"""Alavette Form V1.0 — Windows GUI packaging configuration.

Produces a Windows ``onedir`` GUI release (no console window) suitable for
Windows 10 and Windows 11.  The bundle layout is compatible with the runtime
expectations of the source tree:

- ``src/config/*._PROJECT_ROOT`` resolves to ``Path(__file__).resolve().parents[2]``;
  PyInstaller preserves the ``src/...`` layout under ``_MEIPASS`` so the
  ``config_library`` data files must live at the bundle root next to ``src``.
- ``src/services/problem_report.application_roots`` already adds
  ``Path(sys.executable).parent`` and ``Path(sys._MEIPASS)`` to the search
  roots, so the bundled ``licenses/`` catalog is discovered automatically.
- ``src/shared/engine/office_broker_command`` re-invokes ``sys.executable``
  with internal ``--office-*-child`` flags when frozen; the single onedir EXE
  serves both the GUI and the broker child processes.

Build (on a Windows 10/11 machine with Python 3.10–3.12):

    pyinstaller --noconfirm --clean Alavette-Form_V1.0.spec

The distributable folder is emitted under ``dist/Alavette-Form/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_submodules,
    collect_dynamic_libs,
)


PROJECT_ROOT = Path(SPECPATH).resolve()

# --- Data files --------------------------------------------------------------
# (source_on_disk, destination_inside_bundle) tuples.

datas: list[tuple[str, str]] = []

# 1. Bundled source data: app_icon.png, app_logo.svg and any other non-.py
#    resources shipped alongside the Python package.  PyInstaller preserves
#    the ``src/...`` directory layout under ``_MEIPASS``.
datas += collect_data_files("src")

# 2. Built-in scene / template / master resources referenced via
#    ``src/config/builtin_scenes._CANONICAL_SCENE_ROOT`` and
#    ``src/config/builtin_templates._CANONICAL_TEMPLATE_ROOT``.
datas.append((str(PROJECT_ROOT / "config_library"), "config_library"))

# 3. Template-authoring prompt assets used by the authoring workspace.
datas.append((str(PROJECT_ROOT / "defaults"), "defaults"))

# 4. Third-party license catalog consumed by ``src/services/license_catalog``.
#    Discovered via ``application_roots()`` which already includes the bundle
#    root when frozen.
datas.append((str(PROJECT_ROOT / "licenses"), "licenses"))

# 5. Top-level legal documents required for source-derived redistribution.
for legal_name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md"):
    legal_path = PROJECT_ROOT / legal_name
    if legal_path.is_file():
        datas.append((str(legal_path), "."))

# --- Hidden imports ----------------------------------------------------------

hiddenimports: list[str] = []

# Lazy / PEP 562 module lookups used throughout the UI layer
# (``panel_registry.create_panel``, ``src.shared.ui.__getattr__``,
# ``src.ui.panels.workbench.panel_v2`` detail controllers, the assistant
# provider facade, etc.).  Static import analysis cannot see them, so the
# whole ``src`` package is collected.
hiddenimports += collect_submodules("src")

# pywin32 is imported lazily by the COM automation, secret-store and
# Office broker paths; PyInstaller's built-in hook covers ``pythoncom`` and
# ``win32com`` but a few companion modules need an explicit nudge so the
# frozen exe does not fail at runtime on a stripped Win10 install.
hiddenimports += [
    "win32timezone",
    "win32cred",
    "win32api",
    "win32con",
    "win32process",
    "win32gui",
    "win32security",
    "pywintypes",
    "pythoncom",
    "win32com",
    "win32com.client",
]

# markdown-it-py loads table plugins dynamically; pull the whole package in
# so the markdown importer keeps working in the bundle.
hiddenimports += collect_submodules("markdown_it")

# latex2mathml.converter is imported lazily inside formula_core.convert.
hiddenimports += collect_submodules("latex2mathml")

# --- Native binaries ---------------------------------------------------------

binaries: list[tuple[str, str]] = []
# Ensure pypdfium2's binary data files (PDF rendering blobs) ship with the
# bundle; PyInstaller's pypdfium2 hook covers most of this but the explicit
# collect guards against a future hook regression.
binaries += collect_dynamic_libs("pypdfium2")

# --- Excluded modules (reduce bundle size) -----------------------------------

excludes = [
    "tkinter",
    "unittest",
    "pydoc_data",
    "pydoc",
    "doctest",
    "pytest",
    "_pytest",
    "IPython",
    "matplotlib",
    "numpy",
    "scipy",
    "pandas",
    "PySide6.QtQml",  # application uses QtWidgets/QtSvg/QtNetwork only
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtSerialPort",
    "PySide6.QtSensors",
    "PySide6.QtSerialBus",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSpeech",
    "PySide6.QtTest",
    "PySide6.QtUiTools",
    "PySide6.QtHelp",
    "PySide6.QtDesigner",
]

# --- Build the Analysis ------------------------------------------------------

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    cipher=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --- Build the EXE -----------------------------------------------------------
# Win10 GUI release: console=False to suppress the background terminal window.
# argv_emulation stays off because office broker children read sys.argv
# verbatim, and any Cocoa-style rewriting is irrelevant on Windows.

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Alavette-Form",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# --- COLLECT (onedir layout) -------------------------------------------------
# A folder layout is preferred for the Win10 GUI release: faster startup,
# smaller per-user disk footprint than one-file mode, and easier diagnostic
# access to logs / config roots.

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Alavette-Form",
)
