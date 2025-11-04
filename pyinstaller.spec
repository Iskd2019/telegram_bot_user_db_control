
# Optional spec for finer control. Build with: pyinstaller pyinstaller.spec
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from pathlib import Path

block_cipher = None

pkgs = ["flask", "sqlalchemy", "jinja2", "werkzeug", "psycopg2"]
datas, binaries, hiddenimports = [], [], []

for pkg in pkgs:
    da, bi, hi = collect_all(pkg)
    datas += da; binaries += bi; hiddenimports += hi

proj_dir = Path(__file__).resolve().parent
if (proj_dir / "templates").exists():
    datas.append((str(proj_dir / "templates"), "templates"))
if (proj_dir / "static").exists():
    datas.append((str(proj_dir / "static"), "static"))

a = Analysis(
    ['app.py'],
    pathex=[str(proj_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='TelegramAdminApp', console=True)
