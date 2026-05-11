# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for a one-file Windows build of BeatVideoCutter.

Run on a Windows host:
    pyinstaller --noconfirm BeatVideoCutter.spec
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = []
hiddenimports = []

# librosa pulls in numba/scipy/audioread/soundfile — collect data + submodules.
datas += collect_data_files("librosa")
datas += collect_data_files("soundfile")
datas += collect_data_files("imageio_ffmpeg")

hiddenimports += collect_submodules("librosa")
hiddenimports += collect_submodules("soundfile")
hiddenimports += collect_submodules("audioread")
hiddenimports += collect_submodules("moviepy")
hiddenimports += [
    "sklearn.utils._typedefs",
    "sklearn.utils._heap",
    "sklearn.utils._sorting",
    "sklearn.utils._vector_sentinel",
    "sklearn.neighbors._partition_nodes",
    "scipy.special.cython_special",
]


block_cipher = None


a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "tornado",
        "IPython",
        "notebook",
        "jupyter",
        "pytest",
        "pandas.tests",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BeatVideoCutter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
