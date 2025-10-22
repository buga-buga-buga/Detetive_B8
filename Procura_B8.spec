a = Analysis(
    ['tela_principal.py'],
    pathex=['.'],
    binaries=[],
    datas=[('logo.png', '.'), ('logo.ico', '.')],   # Adiciona os arquivos dentro do executavel
    hiddenimports=['splash_screen', 'procura_B8', '__init__'],  # Tem que incluir na marra!
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='procura_B8',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                                      # Da alerta no trampo se usar 
    upx_exclude=[],
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.rc',                           # Informações pra colocar nas propriedades do executavel
    icon='logo.ico', 
)
