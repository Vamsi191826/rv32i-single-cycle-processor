"""Small two-pass assembler for canonical RV32I source; Python standard library only.
This intentionally excludes macros, linking, sections other than .text, and ELF.
Use GNU tools for larger programs. .hex files contain one 32-bit word per line.
"""
from pathlib import Path
import re
R_OPS = {"add":(0,0), "sub":(0,0x20), "sll":(1,0), "slt":(2,0),
         "sltu":(3,0), "xor":(4,0), "srl":(5,0), "sra":(5,0x20), "or":(6,0), "and":(7,0)}
I_OPS = {"addi":0,"slti":2,"sltiu":3,"xori":4,"ori":6,"andi":7}
LOADS = {"lb":0,"lh":1,"lw":2,"lbu":4,"lhu":5}
STORES = {"sb":0,"sh":1,"sw":2}
BRANCHES = {"beq":0,"bne":1,"blt":4,"bge":5,"bltu":6,"bgeu":7}
ALIASES = dict(zip("zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6".split(),range(32)))
ALIASES["fp"] = 8
def reg(text):
    text = text.lower()
    value = int(text[1:]) if re.fullmatch(r"x\d+",text) else ALIASES[text]
    if not 0 <= value < 32: raise ValueError(f"Invalid register {text}")
    return value
def signed_field(value,bits,even=False):
    if not -(1<<(bits-1)) <= value < (1<<(bits-1)) or (even and value & 1):
        raise ValueError(f"Immediate {value} does not fit signed {bits}-bit field")
    return value & ((1<<bits)-1)
def assemble(text):
    labels, entries = {}, []
    for lineno,line in enumerate(text.splitlines(),1):
        line = line.split("#",1)[0].strip()
        if not line: continue
        if ":" in line:
            name,line = line.split(":",1)
            if name.strip() in labels: raise ValueError(f"Duplicate label {name}")
            labels[name.strip()] = 4*len(entries)
            line = line.strip()
        if not line: continue
        if line.startswith((".text",".globl",".global")): continue
        entries.append((lineno,line))
    words = []
    for index,(lineno,line) in enumerate(entries):
        pc = index*4
        tokens = line.replace(","," ").split()
        op,args = tokens[0].lower(),tokens[1:]
        try:
            def target(arg):
                if arg.startswith("."): return int(arg[1:],0) # GNU-compatible .+N / .-N
                return labels[arg]-pc if arg in labels else int(arg,0)-pc
            if op == ".word": word = int(args[0],0)&0xffffffff
            elif op == "nop": word = 0x13
            elif op in ("ecall","ebreak","fence"):
                word = {"ecall":0x73,"ebreak":0x100073,"fence":0x0ff0000f}[op]
            elif op in R_OPS:
                rd,rs1,rs2 = map(reg,args); f3,f7 = R_OPS[op]
                word = f7<<25 | rs2<<20 | rs1<<15 | f3<<12 | rd<<7 | 0x33
            elif op in I_OPS:
                rd,rs1 = map(reg,args[:2]); imm = signed_field(int(args[2],0),12)
                word = imm<<20 | rs1<<15 | I_OPS[op]<<12 | rd<<7 | 0x13
            elif op in ("slli","srli","srai"):
                rd,rs1 = map(reg,args[:2]); sh = int(args[2],0)
                if not 0 <= sh < 32: raise ValueError("Shift must be 0..31")
                f3 = 1 if op == "slli" else 5; f7 = 0x20 if op == "srai" else 0
                word = f7<<25 | sh<<20 | rs1<<15 | f3<<12 | rd<<7 | 0x13
            elif op in LOADS or op in STORES or op == "jalr":
                match = re.fullmatch(r"([^()]+)\(([^()]+)\)",args[1])
                if not match: raise ValueError("Use offset(register) addressing")
                imm = signed_field(int(match[1],0),12); rs1 = reg(match[2]); r = reg(args[0])
                if op in STORES:
                    word = (imm>>5)<<25 | r<<20 | rs1<<15 | STORES[op]<<12 | (imm&31)<<7 | 0x23
                else:
                    word = imm<<20 | rs1<<15 | (LOADS[op] if op in LOADS else 0)<<12 | r<<7 | (0x03 if op in LOADS else 0x67)
            elif op in BRANCHES:
                rs1,rs2 = map(reg,args[:2]); imm = signed_field(target(args[2]),13,True)
                word = ((imm>>12)&1)<<31 | ((imm>>5)&63)<<25 | rs2<<20 | rs1<<15 | BRANCHES[op]<<12 | ((imm>>1)&15)<<8 | ((imm>>11)&1)<<7 | 0x63
            elif op == "jal":
                rd = reg(args[0]); imm = signed_field(target(args[1]),21,True)
                word = ((imm>>20)&1)<<31 | ((imm>>1)&1023)<<21 | ((imm>>11)&1)<<20 | ((imm>>12)&255)<<12 | rd<<7 | 0x6f
            elif op in ("lui","auipc"):
                rd = reg(args[0]); imm = int(args[1],0)
                if not 0 <= imm <= 0xfffff: raise ValueError("Upper immediate must be 0..0xfffff")
                word = imm<<12 | rd<<7 | (0x37 if op == "lui" else 0x17)
            else: raise ValueError(f"Unsupported mnemonic {op}")
            words.append(word & 0xffffffff)
        except (ValueError,KeyError,IndexError) as exc:
            raise ValueError(f"Line {lineno}: {line}: {exc}") from exc
    return words
def write_hex(words,path):
    Path(path).write_text("".join(f"{word:08x}\n" for word in words),encoding="ascii")
if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("source"); p.add_argument("output")
    a=p.parse_args(); write_hex(assemble(Path(a.source).read_text()),a.output)
