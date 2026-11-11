# PyInstaller tanımı: pyinstaller turnusol.spec
import sys
from PyInstaller.utils.hooks import collect_data_files

veri = []
for klasor in ('yerlesimler', 'formlar', 'sablonlar', 'gui/fontlar', 'gui/ikonlar', 'gui/kilavuz'):
    veri.append((f'turnusol/{klasor}', f'turnusol/{klasor}'))
veri += collect_data_files('pypdfium2_raw') + collect_data_files('pypdfium2')

a = Analysis(['baslat.py'], pathex=['.'], datas=veri,
             hiddenimports=['xlrd', 'openpyxl', 'pypdfium2', 'PySide6.QtPrintSupport'],
             excludes=['tkinter', 'matplotlib', 'PySide6.QtWebEngineCore', 'PySide6.QtQml', 'PySide6.QtQuick'],
             noarchive=False)
pyz = PYZ(a.pure)
ikon = 'turnusol/gui/ikonlar/turnusol.icns' if sys.platform == 'darwin' else 'turnusol/gui/ikonlar/turnusol.ico'
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Turnusol', console=False, icon=ikon,
          upx=False, argv_emulation=False)
coll = COLLECT(exe, a.binaries, a.datas, name='Turnusol', upx=False)
if sys.platform == 'darwin':
    from turnusol import __version__
    app = BUNDLE(coll, name='Turnusol.app', icon=ikon, bundle_identifier='tr.turnusol.okuyucu',
                 info_plist={'CFBundleDisplayName': 'Turnusol', 'CFBundleShortVersionString': __version__,
                             'CFBundleVersion': __version__, 'NSHighResolutionCapable': True,
                             'LSMinimumSystemVersion': '12.0'})
