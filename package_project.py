"""Create a source/evidence ZIP, omitting reproducible tool intermediates."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
def keep(path):
    rel=path.relative_to(ROOT); parts=rel.parts
    if "build" in parts or "__pycache__" in parts or path.suffix in (".pyc",".vvp"): return False
    if parts[:2]==("results","user_runs") and rel.as_posix()!="results/user_runs/README.md": return False
    if parts[:3]==("results","verified","gnu") and path.suffix in (".o",".elf",".bin"): return False
    return rel.as_posix()!="SHA256SUMS.txt"
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=ROOT.parent/(ROOT.name+".zip"))
    a=p.parse_args(); paths=[f for f in sorted(ROOT.rglob("*")) if f.is_file() and keep(f)]
    checksums="".join(hashlib.sha256(f.read_bytes()).hexdigest()+"  "+f.relative_to(ROOT).as_posix()+"\n" for f in paths)
    (ROOT/"SHA256SUMS.txt").write_text(checksums,encoding="ascii")
    paths.append(ROOT/"SHA256SUMS.txt")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path in paths: z.write(path,ROOT.name+"/"+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(a.output) as z:
        bad=z.testzip()
        if bad: raise RuntimeError("ZIP CRC failure: "+bad)
    checksum=hashlib.sha256(a.output.read_bytes()).hexdigest()
    a.output.with_suffix(".zip.sha256").write_text(checksum+"  "+a.output.name+"\n")
    print(f"ZIP PASS: {len(paths)} files, {a.output.stat().st_size:,} bytes")
    print(f"SHA256: {checksum}")
if __name__=="__main__": main()

