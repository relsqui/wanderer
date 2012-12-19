# -*- mode: python -*-
a = Analysis(['wanderer.py'],
             pathex=['/home/fizz/wanderer'],
             hiddenimports=[],
             hookspath=None)
a.datas += Tree('wanderer/data', prefix='data')
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts + [('O', '', 'OPTION')],
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('wanderer-linux'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
app = BUNDLE(exe,
             name=os.path.join('wanderer-mac.app'))
