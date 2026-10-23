"""Optional independent machine-code check against GNU RISC-V assembler/linker."""
from pathlib import Path
import argparse,json,subprocess
from rv32i_asm import assemble
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(); p.add_argument("--prefix",default="riscv64-linux-gnu-"); p.add_argument("--output",type=Path,default=ROOT/"results/user_runs/gnu")
    a=p.parse_args(); out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True); checked=[]
    for source in sorted((ROOT/"programs").glob("*.S")):
        obj=out/(source.stem+".o"); elf=out/(source.stem+".elf"); binary=out/(source.stem+".bin")
        for cmd in ([a.prefix+"as","-march=rv32i","-mabi=ilp32","-mno-relax",str(source),"-o",str(obj)],
                    [a.prefix+"ld","-m","elf32lriscv","--no-relax","-Ttext=0","--entry=0",str(obj),"-o",str(elf)],
                    [a.prefix+"objcopy","-O","binary","-j",".text",str(elf),str(binary)]):
            r=subprocess.run(cmd,capture_output=True,text=True)
            if r.returncode: raise RuntimeError(r.stderr)
        expected=b"".join(w.to_bytes(4,"little") for w in assemble(source.read_text()))
        if binary.read_bytes()!=expected: raise RuntimeError(f"GNU/custom assembler mismatch: {source.name}")
        checked.append(source.name)
    version=subprocess.run([a.prefix+"as","--version"],capture_output=True,text=True,check=True).stdout.splitlines()[0]
    result={"status":"PASS","tool_version":version,"programs_checked":len(checked),"programs":checked}
    (out/"gnu_assembler_check.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"GNU assembler comparison PASS: {len(checked)} programs")
if __name__=="__main__": main()
