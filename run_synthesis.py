"""Optional portable Yosys core synthesis and structural checks; not Vivado timing."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,default=ROOT/"results/user_runs/yosys"); a=p.parse_args()
    out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    sources=[f for f in sorted((ROOT/"rtl").glob("*.v")) if f.stem not in ("rv32i_memory","rv32i_system")]
    q=lambda f:json.dumps(str(f).replace("\\","/"))
    script="read_verilog -I"+q(ROOT/"rtl")+" "+" ".join(map(q,sources))+"; "
    script+="hierarchy -check -top rv32i_core; proc; opt; check -assert; select -assert-none t:$dlatch t:$adlatch; "
    script+="synth -top rv32i_core; check -assert; tee -o statistics.json stat -json; write_json netlist.json"
    r=subprocess.run([os.environ.get("YOSYS","yosys"),"-Q","-p",script],cwd=out,capture_output=True,text=True)
    (out/"synthesis.log").write_text(r.stdout+r.stderr)
    if r.returncode: raise RuntimeError((r.stdout+r.stderr)[-5000:])
    version=subprocess.run([os.environ.get("YOSYS","yosys"),"-V"],capture_output=True,text=True,check=True).stdout.strip()
    hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources+[ROOT/"rtl/rv32i_defs.vh"]}
    (out/"synthesis_summary.json").write_text(json.dumps({"status":"PASS","tool":"Yosys","version":version,"scope":"core only, generic synthesis; no FPGA placement/timing", "latches_inferred":0,"source_sha256":hashes},indent=2)+"\n")
    print("Yosys synthesis/check PASS; no inferred latches")
if __name__=="__main__": main()
