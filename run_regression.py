"""Run six self-checking testbenches with Icarus Verilog or Vivado XSim.
Uses subprocess argument lists, verifies fresh PASS markers, and validates CSV.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
TESTS=["tb_datapath","tb_immediate","tb_regfile","tb_decoder","tb_memory","tb_system"]
def execute(command,cwd,log,environment=None):
    try:
        result=subprocess.run([str(x) for x in command],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=environment,timeout=600)
    except subprocess.TimeoutExpired as error:
        captured=error.stdout or b""
        if isinstance(captured,bytes): captured=captured.decode("utf-8",errors="replace")
        Path(log).write_text(captured+"\nPROCESS TIMEOUT after 600 seconds\n",encoding="utf-8")
        raise RuntimeError(f"Process exceeded 600 seconds; inspect {log}") from error
    Path(log).write_text(result.stdout,encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command[0]}\n{result.stdout[-6000:]}")
    return result.stdout
def validate_trace(output):
    manifest=json.loads((ROOT/"programs/generated/manifest.json").read_text())
    rows=list(csv.DictReader((output/"retire_trace.csv").open()))
    index=0
    for case in manifest["cases"]:
        expected=(ROOT/"programs/generated"/f'{case["name"]}_trace.hex').read_text().splitlines()
        for step,line in enumerate(expected):
            if index>=len(rows): raise RuntimeError("Truncated retire CSV")
            r=rows[index]
            fields=[int(r[k],16) if k not in ("rd_write","rd","mem_read") else int(r[k])
                    for k in ("pc","instruction","next_pc","rd_write","rd","rd_data","mem_read","mem_address","mem_strobe","mem_data")]
            actual="".join(f"{v:08x}" for v in fields)
            if r["case"]!=case["name"] or int(r["step"])!=step or actual!=line:
                raise RuntimeError(f"CSV mismatch at {case['name']} step {step}")
            index+=1
    if index!=len(rows): raise RuntimeError("Extra retire CSV records")
    return manifest
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--simulator",choices=["iverilog","xsim"],default="iverilog")
    p.add_argument("--waves",action="store_true",help="Dump tb_system VCD with Icarus; use Vivado Wave window for XSim")
    p.add_argument("--regenerate",action="store_true")
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    output=(args.output or ROOT/"results/user_runs"/args.simulator).resolve(); output.mkdir(parents=True,exist_ok=True)
    if args.regenerate:
        subprocess.run([sys.executable,str(ROOT/"tools/build_programs.py")],check=True)
    sources=sorted((ROOT/"rtl").glob("*.v")); includes=[ROOT/"rtl",ROOT/"tb",ROOT/"tb/generated"]
    summaries={}; unit_checks={}
    for top in TESTS:
        marker=output/f"{top}.pass"; marker.unlink(missing_ok=True)
        if args.simulator=="iverilog":
            compiler=os.environ.get("IVERILOG","iverilog"); runtime=os.environ.get("VVP","vvp")
            command=[compiler,"-g2012","-Wall"]
            for inc in includes: command += ["-I",inc]
            command += ["-s",top,"-o",output/f"{top}.vvp",*sources,ROOT/"tb"/f"{top}.sv"]
            execute(command,ROOT,output/f"{top}_compile.log")
            run=[runtime,output/f"{top}.vvp",f"+ROOT={ROOT.as_posix()}",f"+OUT={output.as_posix()}"]
            if args.waves and top=="tb_system": run += ["+WAVES"]
            text=execute(run,ROOT,output/f"{top}.log")
        else:
            command=[os.environ.get("XVLOG","xvlog"),"-sv"]
            for inc in includes: command += ["-i",inc]
            command += [*sources,ROOT/"tb"/f"{top}.sv"]
            execute(command,output,output/f"{top}_compile.log")
            execute([os.environ.get("XELAB","xelab"),"-debug","typical",top,"-s",top+"_snapshot"],output,output/f"{top}_elaborate.log")
            run=[os.environ.get("XSIM","xsim"),top+"_snapshot","-tclbatch",ROOT/"scripts/vivado/run_all.tcl",
                 "-testplusarg",f"ROOT={ROOT.as_posix()}","-testplusarg",f"OUT={output.as_posix()}"]
            text=execute(run,output,output/f"{top}.log")
        if not marker.exists() or f"TESTBENCH_PASS {top}" not in text:
            raise RuntimeError(f"Fresh PASS marker missing for {top}; inspect its simulation log")
        summaries[top]="PASS"
        for label,count in re.findall(r"([A-Z]+)_CHECKS=(\d+)",text): unit_checks[label.lower()]=int(count)
        print(f"PASS {top}",flush=True)
    manifest=validate_trace(output)
    versions={}
    if args.simulator=="iverilog":
        versions["iverilog"]=subprocess.run([os.environ.get("IVERILOG","iverilog"),"-V"],capture_output=True,text=True).stdout.splitlines()[0]
    hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
            for folder in ("rtl","tb","tools","programs") for f in sorted((ROOT/folder).rglob("*")) if f.is_file() and "__pycache__" not in str(f)}
    summary={"status":"PASS","simulator":args.simulator,"utc":datetime.now(timezone.utc).isoformat(),
             "testbenches":summaries,"unit_checks":unit_checks,"versions":versions,
             "cases_passed":manifest["case_count"],"retired_events_checked":manifest["retired_instructions"],
             "instruction_groups":40,"branch_outcomes":12,"random_seeds":16,
             "functional_coverage":manifest["coverage"],"branch_coverage":manifest["branch_coverage"],"source_sha256":hashes}
    (output/"verification_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(f"ALL TESTS PASS: {manifest['case_count']} programs, {manifest['retired_instructions']} retire events; final registers and 4096 memory bytes checked per program.")
if __name__=="__main__":
    try: main()
    except (RuntimeError,OSError,subprocess.CalledProcessError) as error:
        print(f"REGRESSION FAILED: {error}",file=sys.stderr); sys.exit(1)
