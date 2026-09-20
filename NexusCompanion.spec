# Reproducible allowlist: never include settings, databases, caches or screenshots.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules
root=Path(SPECPATH)
datas=[(str(root/'assets'),'assets'),(str(root/'.replay-deps'),'.replay-deps')]
for name in ('build_catalogue.json','draft_catalogue.json','README.md','THIRD_PARTY.md'):
    datas.append((str(root/name),'.'))
import sys
datas.append((str(Path(sys.base_prefix)/'LICENSE.txt'),'licenses/python'))
for path in (root/'.packaging-deps').glob('pyinstaller-*.dist-info/licenses'):
    datas.append((str(path),'licenses/pyinstaller'))
# Projection DLLs and import-time namespace discovery need the original tree.
datas.append((str(root/'.deps'/'winrt'),'winrt'))
for path in (root/'.deps').glob('*.dist-info'):
    datas.append((str(path),'licenses/'+path.name))
binaries=[];hidden=[]
for package in ('windows_capture','winrt','PIL','numpy','cv2'):
    d,b,h=collect_all(package);datas+=d;binaries+=b;hidden+=h
a=Analysis([str(root/'launcher.py')],pathex=[str(root),str(root/'.deps'),str(root/'.replay-deps')],
           binaries=binaries,datas=datas,hiddenimports=hidden+['preview_ui','six','mpyq','heroprotocol.decoders'],
           excludes=['pytest','unittest','pydoc','test'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='NexusCompanion',console=False,
        icon=str(root/'assets'/'ui'/'nexus.ico'))
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='NexusCompanion')
