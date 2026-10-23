"""Architectural RV32I interpreter, independent of RTL/internal control encodings.
The reference updates architectural registers and individual memory bytes.
It is a project oracle, not Spike or an official RISC-V compliance suite.
"""
from collections import Counter
MASK = 0xffffffff
def u32(x): return x & MASK
def signed(x,bits=32):
    x &= (1<<bits)-1
    return x-(1<<bits) if x & (1<<(bits-1)) else x
class Trap(Exception):
    def __init__(self,cause,value=0,name="FAULT"):
        self.cause,self.value,self.name = cause,u32(value),name
class Model:
    def __init__(self,words,imem_words=1024,dmem_bytes=4096):
        if len(words)>imem_words: raise ValueError("Program exceeds instruction memory")
        self.program=list(words)+[0x13]*(imem_words-len(words))
        self.memory=bytearray(dmem_bytes); self.regs=[0]*32; self.pc=0
        self.coverage=Counter(); self.branch_coverage=Counter(); self.trace=[]
    def step(self):
        pc=self.pc
        if pc & 3: raise Trap(0,pc)
        if pc>=len(self.program)*4: raise Trap(1,pc)
        ins=self.program[pc//4]
        op=ins&127; rd=(ins>>7)&31; f=(ins>>12)&7; r1=(ins>>15)&31; r2=(ins>>20)&31; f7=ins>>25
        a,b=self.regs[r1],self.regs[r2]
        imm=signed(ins>>20,12)
        nxt=u32(pc+4); value=None; name="ILLEGAL"
        mem_read=0; addr=0; strobe=0; bus_data=0; branch=None
        if op==0x33:
            legal={(0,0):"ADD",(0,32):"SUB",(1,0):"SLL",(2,0):"SLT",(3,0):"SLTU",(4,0):"XOR",(5,0):"SRL",(5,32):"SRA",(6,0):"OR",(7,0):"AND"}
            name=legal.get((f,f7),"ILLEGAL")
            if name=="ILLEGAL": raise Trap(2,ins,name)
            if name=="ADD": value=a+b
            elif name=="SUB": value=a-b
            elif name=="SLL": value=a<<(b&31)
            elif name=="SLT": value=int(signed(a)<signed(b))
            elif name=="SLTU": value=int(a<b)
            elif name=="XOR": value=a^b
            elif name=="SRL": value=a>>(b&31)
            elif name=="SRA": value=signed(a)>>(b&31)
            elif name=="OR": value=a|b
            else: value=a&b
        elif op==0x13:
            names={0:"ADDI",2:"SLTI",3:"SLTIU",4:"XORI",6:"ORI",7:"ANDI"}
            if f in names:
                name=names[f]
                if f==0: value=a+imm
                elif f==2: value=int(signed(a)<imm)
                elif f==3: value=int(a<u32(imm))
                elif f==4: value=a^u32(imm)
                elif f==6: value=a|u32(imm)
                else: value=a&u32(imm)
            elif f==1 and f7==0: name="SLLI"; value=a<<r2
            elif f==5 and f7 in (0,32):
                name="SRAI" if f7==32 else "SRLI"
                value=(signed(a)>>r2) if f7==32 else (a>>r2)
            else: raise Trap(2,ins,"ILLEGAL")
        elif op in (0x03,0x23):
            if op==0x03:
                defs={0:("LB",1,True),1:("LH",2,True),2:("LW",4,True),4:("LBU",1,False),5:("LHU",2,False)}
                if f not in defs: raise Trap(2,ins,"ILLEGAL")
                name,width,sext=defs[f]; mem_read=1
            else:
                defs={0:("SB",1),1:("SH",2),2:("SW",4)}
                if f not in defs: raise Trap(2,ins,"ILLEGAL")
                name,width=defs[f]
                imm=signed(((ins>>25)<<5)|((ins>>7)&31),12)
            addr=u32(a+imm)
            if addr%width: raise Trap(4 if op==3 else 6,addr,name)
            if addr+width>len(self.memory): raise Trap(5 if op==3 else 7,addr,name)
            if op==3:
                raw=int.from_bytes(self.memory[addr:addr+width],"little")
                value=signed(raw,width*8) if sext else raw
            else:
                # Architectural store writes individual bytes, independent of bus masking.
                for k in range(width): self.memory[addr+k]=(b>>(8*k))&255
                strobe=((1<<width)-1)<<(addr&3); bus_data=u32(b<<(8*(addr&3)))
        elif op==0x63:
            names={0:"BEQ",1:"BNE",4:"BLT",5:"BGE",6:"BLTU",7:"BGEU"}
            if f not in names: raise Trap(2,ins,"ILLEGAL")
            name=names[f]
            offset=signed(((ins>>31)<<12)|(((ins>>7)&1)<<11)|(((ins>>25)&63)<<5)|(((ins>>8)&15)<<1),13)
            branch={0:a==b,1:a!=b,4:signed(a)<signed(b),5:signed(a)>=signed(b),6:a<b,7:a>=b}[f]
            if branch: nxt=u32(pc+offset)
        elif op==0x37: name="LUI"; value=ins&0xfffff000
        elif op==0x17: name="AUIPC"; value=pc+(ins&0xfffff000)
        elif op==0x6f:
            name="JAL"; value=pc+4
            offset=signed(((ins>>31)<<20)|(((ins>>12)&255)<<12)|(((ins>>20)&1)<<11)|(((ins>>21)&1023)<<1),21)
            nxt=u32(pc+offset)
        elif op==0x67 and f==0:
            name="JALR"; value=pc+4; nxt=u32(a+imm)&0xfffffffe
        elif op==0x0f and f==0: name="FENCE"
        elif ins==0x73: raise Trap(11,0,"ECALL")
        elif ins==0x100073: raise Trap(3,0,"EBREAK")
        else: raise Trap(2,ins,"ILLEGAL")
        if nxt & 3: raise Trap(0,nxt,name)
        write=int(value is not None and rd!=0)
        if write: self.regs[rd]=u32(value)
        self.regs[0]=0; self.pc=nxt
        fields=[pc,ins,nxt,write,rd if write else 0,u32(value) if write else 0,
                mem_read,addr,strobe,bus_data]
        self.trace.append(fields); self.coverage[name]+=1
        if branch is not None: self.branch_coverage[f"{name}_{'TAKEN' if branch else 'NOT_TAKEN'}"]+=1
        return fields
    def run(self,max_steps=20000):
        for _ in range(max_steps):
            try: self.step()
            except Trap as fault:
                self.coverage[fault.name]+=1
                return {"cause":fault.cause,"pc":self.pc,"value":fault.value,"name":fault.name}
        raise RuntimeError("Reference program did not terminate within the step limit")
def pack_trace(fields): return "".join(f"{u32(value):08x}" for value in fields)
