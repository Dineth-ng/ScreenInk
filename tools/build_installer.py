"""Compile a per-user installer; requires the verified one-folder build."""
import argparse,hashlib,os,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from screenink.version import __version__


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--iscc');args=parser.parse_args()
    compiler=args.iscc or shutil.which('ISCC')
    if not compiler:
        for location in (Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Inno Setup 6/ISCC.exe', ROOT/'build/tools/InnoSetup/ISCC.exe'):
            if location.is_file():compiler=str(location);break
    if not compiler:raise SystemExit('Install Inno Setup from jrsoftware.org or pass --iscc PATH.')
    if not (ROOT/'dist/ScreenInk/ScreenInk.exe').is_file():raise SystemExit('Build tools/build_beta.py first.')
    subprocess.run([compiler,f'/DAppVersion={__version__}',str(ROOT/'packaging/ScreenInk.iss')],check=True,cwd=ROOT)
    output=ROOT/'release'/f'ScreenInk-Setup-{__version__}.exe'
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.sha256').write_text(f'{digest}  {output.name}\n')
    print(output)

if __name__=='__main__':main()
