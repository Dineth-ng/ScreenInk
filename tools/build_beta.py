"""Build and zip a portable Windows beta using the current virtual environment."""

import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from screenink.version import __version__


def main():
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("Build this Windows x64 beta on Windows x64.")
    subprocess.run([sys.executable, str(ROOT / "tools/generate_icon.py")], cwd=ROOT, check=True)
    build_environment = os.environ.copy()
    # Avoid collecting unrelated Qt/ICU DLLs from tools on the caller's PATH.
    windows = Path(os.environ.get("SystemRoot", "C:/Windows"))
    build_environment["PATH"] = os.pathsep.join(map(str, (
        Path(sys.executable).parent, Path(sys.base_prefix), windows / "System32", windows,
    )))
    from version_metadata import generate
    generate()
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
                    "ScreenInk.spec"], cwd=ROOT, env=build_environment, check=True)
    distribution = ROOT / "dist/ScreenInk"
    # Load the same Microsoft runtime as bundled Python before system DLLs.
    # These must sit beside the bootloader, as well as inside _internal.
    for name in ("vcruntime140.dll", "vcruntime140_1.dll"):
        shutil.copyfile(distribution / "_internal" / name, distribution / name)
    smoke_environment = os.environ.copy()
    smoke_environment["PATH"] = os.pathsep.join(map(str, (windows / "System32", windows)))
    for key in ("PYTHONHOME", "PYTHONPATH", "QT_PLUGIN_PATH", "QML2_IMPORT_PATH"):
        smoke_environment.pop(key, None)
    subprocess.run([str(distribution / "ScreenInk.exe"), "--smoke-test"],
                   cwd=distribution, env=smoke_environment, check=True, timeout=30)
    shutil.copyfile(ROOT / "docs/BETA_TESTING.md", distribution / "START_HERE.txt")
    shutil.copyfile(ROOT / "README.md", distribution / "README.md")
    shutil.copyfile(ROOT / "docs/PRESENTATION.md", distribution / "PRESENTATION.md")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
        shutil.copyfile(ROOT / name, distribution / name)
    shutil.copytree(ROOT / "licenses", distribution / "licenses", dirs_exist_ok=True)
    output = ROOT / "release"
    output.mkdir(exist_ok=True)
    filename = f"ScreenInk-{__version__}-windows-x64"
    archive = Path(shutil.make_archive(str(output / filename), "zip", ROOT / "dist", "ScreenInk"))
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    checksum = archive.with_suffix(".sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(f"\nPortable beta: {archive}\nSHA-256: {digest}")


if __name__ == "__main__":
    main()
