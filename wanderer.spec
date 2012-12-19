# -*- mode: python -*-

a = Analysis(['wanderer.py'],
             pathex=['/home/fizz/pyinstaller-2.0'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.linux2/wanderer', 'wanderer.exe'),
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               Tree("wanderer/data", prefix="data"),
               strip=None,
               upx=True,
               name=os.path.join('dist'))
