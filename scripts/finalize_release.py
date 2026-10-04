from __future__ import annotations
import argparse, hashlib, os, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = {'__pycache__', '.pytest_cache', 'build', '_video_frames'}
RUNTIME_SUFFIXES = {'.pyc', '.pyo', '.db', '.aux', '.log', '.out'}
RUNTIME_FILES = {'.coverage'}

def clean_tree(root: Path) -> None:
    for p in sorted(root.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        if p.is_dir() and (p.name in RUNTIME_DIRS or p.name.endswith('.egg-info')):
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file() and (p.name in RUNTIME_FILES or p.suffix in RUNTIME_SUFFIXES):
            p.unlink(missing_ok=True)

def write_checksums(root: Path) -> int:
    checksum = root / 'SHA256SUMS'
    checksum.unlink(missing_ok=True)
    files = sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    lines=[]
    for p in files:
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f'{h}  {p.relative_to(root).as_posix()}')
    checksum.write_text('\n'.join(lines)+'\n')
    return len(files)

def update_release_contents(root: Path, count: int) -> None:
    p=root/'RELEASE_CONTENTS.md'
    s=p.read_text() if p.exists() else '# Release Contents\n'
    import re
    if 'Validated public research release containing' in s:
        s=re.sub(r'Validated public research release containing \*\*\d+ files\*\* \(excluding the checksum index itself\)\.',
                 f'Validated public research release containing **{count} files** (excluding the checksum index itself).', s)
    else:
        s += f'\nValidated public research release containing **{count} files** (excluding the checksum index itself).\n'
    p.write_text(s)

def make_zip(root: Path, zip_path: Path) -> None:
    zip_path.unlink(missing_ok=True)
    # ZIP requires a DOS timestamp; use a fixed neutral value so archive metadata
    # never exposes the project/release build date.
    neutral_time=(1980,1,1,0,0,0)
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for p in sorted(root.rglob('*')):
            if p.is_file():
                arc=f'{root.name}/{p.relative_to(root).as_posix()}'
                info=zipfile.ZipInfo(arc, date_time=neutral_time)
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(p.stat().st_mode & 0xFFFF) << 16
                zf.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    digest=hashlib.sha256(zip_path.read_bytes()).hexdigest()
    zip_path.with_suffix(zip_path.suffix+'.sha256').write_text(f'{digest}  {zip_path.name}\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('destination', type=Path)
    ap.add_argument('--zip', dest='zip_path', type=Path)
    args=ap.parse_args()
    dest=args.destination.resolve()
    if ROOT == dest or ROOT in dest.parents:
        raise SystemExit('destination must be outside the source repository')
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(ROOT,dest)
    clean_tree(dest)
    count=write_checksums(dest)
    update_release_contents(dest,count)
    # RELEASE_CONTENTS changed after first checksum pass; regenerate checksums.
    count=write_checksums(dest)
    if args.zip_path: make_zip(dest,args.zip_path.resolve())
    print(f'finalized {dest} with {count} files excluding SHA256SUMS')

if __name__=='__main__': main()
