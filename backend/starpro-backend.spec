# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app', 'app'), ('storage', 'storage'), ('.env', '.')],
    hiddenimports=[
        'fastapi', 
        'uvicorn', 
        'sqlalchemy', 
        'aiosqlite', 
        'pydantic', 
        'pillow',
        # 添加可能缺失的隐藏导入
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.wsproto_impl',
        'fastapi.middleware.cors',
        'fastapi.responses',
        'sqlalchemy.dialects.sqlite',
        'pydantic.fields',
        'pydantic.main'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小大小
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy'
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
    name='starpro-backend-arm64',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # CentOS 7可能不支持UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)