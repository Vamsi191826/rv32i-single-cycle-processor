"""Regenerate assembly, ROM images, independent golden traces and regression cases."""
from pathlib import Path
import json,random
from collections import Counter
from rv32i_asm import assemble,write_hex,R_OPS,I_OPS,LOADS,STORES,BRANCHES
from reference_model import Model,pack_trace,u32,signed
ROOT=Path(__file__).resolve().parents[1]
PROG=ROOT/"programs"; GEN=PROG/"generated"; TBGEN=ROOT/"tb"/"generated"
def li(rd,value):
    value=u32(value); high=((value+0x800)>>12)&0xfffff; low=signed(value-(high<<12))
    assert -2048<=low<=2047
    return [f"lui x{rd}, 0x{high:x}",f"addi x{rd}, x{rd}, {low}"]
def directed():
    s=["# Directed instruction, boundary and dependency tests.",".text",".globl _start","_start:"]
    s+=li(5,-1)+li(6,1)+li(7,0x80000000)+li(8,0x7fffffff)+li(9,32)
    s += ["addi x0, x0, 99","add x10, x8, x6","sub x11, x7, x6",
          "and x12, x7, x5","or x13, x7, x6","xor x14, x5, x7",
          "sll x15, x6, x9","srl x16, x7, x6","sra x17, x7, x6",
          "slt x18, x7, x8","sltu x19, x7, x8","addi x10, x10, -2048",
          "slti x11, x7, 0","sltiu x12, x6, -1","xori x13, x6, -1",
          "ori x14, x0, -2048","andi x15, x5, 2047",
          "slli x16, x6, 31","srli x17, x7, 31","srai x18, x7, 31",
          "auipc x19, 0x12345","addi x20, x0, 512"]
    s+=li(21,0x80ff7f01)
    s += ["sw x21, 0(x20)","lb x22, 3(x20)","lbu x23, 3(x20)",
          "lh x24, 2(x20)","lhu x25, 2(x20)","lw x26, 0(x20)"]
    for offset in range(4): s += [f"sb x5, {offset}(x20)",f"lbu x22, {offset}(x20)"]
    s += ["sh x21, 2(x20)","lh x23, 2(x20)","lhu x24, 2(x20)","lw x25, 0(x20)"]
    s += li(27,4092)+["sw x21, 0(x27)","lb x22, 3(x27)","sh x5, 2(x27)","lhu x23, 2(x27)"]
    tests=[("beq",6,6,5,6),("bne",5,6,6,6),("blt",5,6,6,5),
           ("bge",6,5,5,6),("bltu",6,5,5,6),("bgeu",5,6,6,5)]
    for op,a,b,c,d in tests:
        s += [f"{op} x{a}, x{b}, {op}_taken", "addi x4, x4, 100",f"{op}_taken:",
              f"{op} x{c}, x{d}, {op}_not_taken","addi x4, x4, 1",f"{op}_not_taken:"]
    s += ["addi x30, x0, 4","loop:","addi x30, x30, -1","bne x30, x0, loop",
          "jal x1, subroutine","jal x0, after_subroutine","subroutine:",
          "addi x4, x4, 1","jalr x0, 0(x1)","after_subroutine:",
          "auipc x28, 0","addi x28, x28, 17","jalr x28, 0(x28)",
          "addi x4, x4, 100","fence","lw x0, 0(x20)","ebreak"]
    return s
def bubble_sort():
    s=["# Signed ascending bubble sort. Array occupies bytes 256..291.",".text",".globl _start","_start:","addi x20, x0, 256"]
    array=[23,-7,0,99,-100,23,1,0x7fffffff,-2147483648]
    for k,value in enumerate(array): s+=li(5,value)+[f"sw x5, {k*4}(x20)"]
    s += ["addi x6, x0, 8","outer:","addi x7, x0, 0","addi x8, x20, 0","inner:",
          "lw x9, 0(x8)","lw x10, 4(x8)","bge x10, x9, no_swap",
          "sw x10, 0(x8)","sw x9, 4(x8)","no_swap:","addi x8, x8, 4",
          "addi x7, x7, 1","blt x7, x6, inner","addi x6, x6, -1",
          "bne x6, x0, outer","addi x11, x0, 1","sw x11, 0(x0)","ebreak"]
    return s,array
def fibonacci():
    return ["# Store F0..F11 at bytes 128..175.",".text",".globl _start","_start:",
            "addi x5, x0, 0","addi x6, x0, 1","addi x7, x0, 12","addi x8, x0, 128",
            "fib_loop:","sw x5, 0(x8)","add x9, x5, x6","addi x5, x6, 0",
            "addi x6, x9, 0","addi x8, x8, 4","addi x7, x7, -1",
            "bne x7, x0, fib_loop","ebreak"]
def random_program(seed):
    rng=random.Random(seed); s=[f"# Seeded legal RV32I stress program. Seed={seed}",".text",".globl _start","_start:"]
    corners=[0,1,-1,0x80000000,0x7fffffff,31,32,63,0xaaaaaaaa,0x55555555]
    for r in range(1,30): s+=li(r,rng.choice(corners) if r<12 else rng.getrandbits(32))
    s += ["addi x31, x0, 1024"]
    for k in range(400):
        choice=rng.randrange(12); rd=rng.randrange(30); a=rng.randrange(30); b=rng.randrange(30)
        if choice<3:
            op=rng.choice(list(R_OPS)); s += [f"{op} x{rd}, x{a}, x{b}"]
        elif choice<5:
            op=rng.choice(list(I_OPS)); s += [f"{op} x{rd}, x{a}, {rng.randint(-2048,2047)}"]
        elif choice==5:
            op=rng.choice(["slli","srli","srai"]); s += [f"{op} x{rd}, x{a}, {rng.randrange(32)}"]
        elif choice==6:
            op=rng.choice(list(LOADS)+list(STORES)); width=1 if op in ("lb","lbu","sb") else (2 if op in ("lh","lhu","sh") else 4)
            offset=rng.randrange(-128,128)//width*width
            s += [f"{op} x{rd}, {offset}(x31)"]
        elif choice==7:
            op=rng.choice(list(BRANCHES)); label=f"branch_{k}"
            s += [f"{op} x{a}, x{b}, {label}","addi x4, x4, 1",f"{label}:"]
        elif choice==8:
            op=rng.choice(["lui","auipc"]); s += [f"{op} x{rd}, 0x{rng.randrange(1<<20):x}"]
        elif choice==9:
            s += [f"jal x29, jump_{k}","addi x4, x4, 1",f"jump_{k}:"]
        elif choice==10:
            s += ["auipc x28, 0","addi x28, x28, 17","jalr x29, 0(x28)","addi x4, x4, 1"]
        else:
            s += ["addi x30, x0, 3",f"loop_{k}:","addi x30, x30, -1",f"bne x30, x0, loop_{k}"]
    s += ["fence","ebreak"]
    return s
def fault_cases():
    out={"ecall":["addi x1, x0, 123","ecall"],"illegal_word":[".word 0xffffffff"],
         "illegal_fence_i":[".word 0x0000100f"],"illegal_csr":[".word 0x300010f3"],
         "illegal_load_width":[".word 0x00003083"],"illegal_store_width":[".word 0x00103023"],
         "illegal_jalr_funct3":[".word 0x000010e7"],
         "illegal_slli":[".word 0x04001093"],"illegal_srli":[".word 0x02005093"],
         "jal_misaligned":["addi x1, x0, 123","jal x1, .+2"],
         "jalr_misaligned":["addi x1, x0, 123","addi x2, x0, 3","jalr x1, 0(x2)"],
         "imem_access":["jal x1, .+4096"],"imem_negative":["jal x1, .-4"],
         "load_half_misaligned":["lh x1, 1(x0)"],"load_word_misaligned":["lw x1, 2(x0)"],
         "store_half_misaligned":["addi x1, x0, 123","sh x1, 1(x0)"],
         "store_word_misaligned":["addi x1, x0, 123","sw x1, 2(x0)"],
         "load_word_access":li(1,4096)+["lw x2, 0(x1)"],
         "load_byte_access":li(1,4096)+["lb x2, 0(x1)"],
         "load_negative_access":["addi x1, x0, -4","lw x2, 0(x1)"],
         "store_word_access":li(1,4096)+["sw x2, 0(x1)"],
         "store_byte_access":li(1,4096)+["sb x2, 0(x1)"],
         "load_x0_fault":["lw x0, 2(x0)"],
         "branch_misaligned_taken":["beq x0, x0, .+2"],
         "branch_misaligned_not_taken":["bne x0, x0, .+2","ebreak"]}
    for f in range(8):
        word=(1<<25)|(2<<20)|(1<<15)|(f<<12)|(3<<7)|0x33
        out[f"illegal_r_funct7_{f}"]=[f".word 0x{word:08x}"]
    return out
def main():
    GEN.mkdir(exist_ok=True); TBGEN.mkdir(exist_ok=True)
    cases={"directed_isa":directed(),"fibonacci":fibonacci()}
    sort,sort_input=bubble_sort(); cases["bubble_sort"]=sort
    for seed in range(16): cases[f"random_{seed:02d}"]=random_program(0x51c000+seed)
    cases.update(fault_cases())
    manifest=[]; coverage=Counter(); branches=Counter(); calls=[]
    for name,lines in cases.items():
        source="\n".join(lines)+"\n"; (PROG/f"{name}.S").write_text(source,encoding="ascii")
        words=assemble(source); model=Model(words); trap=model.run()
        if name=="bubble_sort":
            got=[signed(int.from_bytes(model.memory[256+4*k:260+4*k],"little")) for k in range(len(sort_input))]
            assert got==sorted(sort_input),got
        if name=="fibonacci":
            got=[int.from_bytes(model.memory[128+4*k:132+4*k],"little") for k in range(12)]
            assert got==[0,1,1,2,3,5,8,13,21,34,55,89],got
        write_hex(words,GEN/f"{name}.hex")
        (GEN/f"{name}_trace.hex").write_text("".join(pack_trace(t)+"\n" for t in model.trace),encoding="ascii")
        write_hex(model.regs,GEN/f"{name}_regs.hex")
        (GEN/f"{name}_memory.hex").write_text("".join(f"{b:02x}\n" for b in model.memory),encoding="ascii")
        record={"name":name,"program_words":len(words),"retired":len(model.trace),"trap":trap,
                "coverage":dict(model.coverage),"branch_coverage":dict(model.branch_coverage)}
        manifest.append(record); coverage.update(model.coverage); branches.update(model.branch_coverage)
        calls.append(f'run_case("{name}", {len(words)}, {len(model.trace)}, 32\'h{trap["cause"]:08x}, 32\'h{trap["pc"]:08x}, 32\'h{trap["value"]:08x});')
    (TBGEN/"case_list.svh").write_text("// Generated by tools/build_programs.py; committed vectors run without Python.\n"+"\n".join(calls)+"\n",encoding="ascii")
    required=set("ADD SUB SLL SLT SLTU XOR SRL SRA OR AND ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI LB LH LW LBU LHU SB SH SW BEQ BNE BLT BGE BLTU BGEU LUI AUIPC JAL JALR FENCE ECALL EBREAK".split())
    assert required<=set(coverage),required-set(coverage)
    for name in BRANCHES:
        assert branches[name.upper()+"_TAKEN"] and branches[name.upper()+"_NOT_TAKEN"]
    result={"case_count":len(manifest),"retired_instructions":sum(c["retired"] for c in manifest),
            "random_seeds":16,"instruction_groups_tested":len(required),"coverage":dict(coverage),
            "branch_coverage":dict(branches),"cases":manifest}
    (GEN/"manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print(f"Built {len(manifest)} programs; {result['retired_instructions']} golden retire events; 40/40 instruction groups; 12/12 branch outcomes")
if __name__=="__main__": main()
