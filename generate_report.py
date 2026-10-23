"""Regenerate engineering diagrams and the project report from actual evidence.

Optional dependencies: matplotlib and reportlab. Simulation needs neither.
The report records project verification; it does not manufacture Vivado results.
"""
from pathlib import Path
import json
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/"docs"
NAVY="#122C46"; TEAL="#087F8C"; BLUE="#266AA6"; GRAY="#536579"; LIGHT="#EDF4F8"
DOCS.mkdir(exist_ok=True)

def node(ax,x,y,w,h,title,detail="",color=NAVY):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.04,rounding_size=0.12",
                               linewidth=1.2,edgecolor=color,facecolor="white",zorder=3))
    title_text=ax.text(x+w/2,y+h*(.69 if detail else .5),title,ha="center",va="center",
                       fontsize=12.5,fontweight="bold",color=color,zorder=4)
    texts=[title_text]
    if detail:
        texts.append(ax.text(x+w/2,y+h*.29,detail,ha="center",va="center",fontsize=11.2,color=GRAY,zorder=4))
    # Keep real font metrics inside every engineering block, including SVG.
    renderer=ax.figure.canvas.get_renderer()
    available=.88*(ax.transData.transform((x+w,y))[0]-ax.transData.transform((x,y))[0])
    for label in texts:
        while label.get_window_extent(renderer).width>available:
            label.set_fontsize(label.get_fontsize()-.25)

def route(ax,points,label="",label_at=None,color=BLUE,dashed=False):
    for start,end in zip(points[:-2],points[1:-1]):
        ax.plot([start[0],end[0]],[start[1],end[1]],color=color,lw=1.3,ls="--" if dashed else "-",zorder=1)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle="-|>",mutation_scale=11,
                                linewidth=1.3,color=color,linestyle="--" if dashed else "-",zorder=2))
    if label and label_at:
        ax.text(*label_at,label,color=color,fontsize=9.8,ha="center",va="center",
                bbox=dict(boxstyle="round,pad=0.16",facecolor="white",edgecolor="none"),zorder=5)

def save_diagram(fig,name):
    fig.savefig(DOCS/(name+".svg"),bbox_inches="tight",facecolor="white")
    fig.savefig(DOCS/(name+".png"),dpi=200,bbox_inches="tight",facecolor="white")
    plt.close(fig)

def diagrams(summary):
    plt.rcParams.update({"font.family":"DejaVu Sans","svg.fonttype":"none"})
    fig,ax=plt.subplots(figsize=(13.8,9.8))
    ax.set_xlim(-.05,13.9); ax.set_ylim(.3,10.1); ax.axis("off")
    node(ax,.45,8.4,2.05,.85,"PC register","rv32i_pc")
    node(ax,3.2,8.4,2.4,.85,"Instruction memory","combinational read")
    node(ax,6.3,8.4,2.45,.85,"Decoder","control signals")
    node(ax,6.3,6.55,2.45,.95,"Immediate generator","I / S / B / U / J")
    node(ax,3.2,4.45,2.4,1.35,"Register file","rs1, rs2 / write rd")
    node(ax,6.3,4.45,2.45,1.35,"ALU operands","A: rs1 / PC / 0\nB: rs2 / immediate")
    node(ax,9.8,4.5,2.1,1.25,"ALU","10 operations")
    node(ax,9.65,1.5,3.05,1.5,"Data memory + lanes","address / shifted rs2 / strobes\naligned-word read")
    node(ax,6.3,1.75,2.45,1.0,"Load extension","byte / halfword / word")
    node(ax,3.2,1.5,2.4,1.5,"Writeback MUX","ALU / load / PC+4",TEAL)
    node(ax,.45,6.45,2.05,.85,"PC + 4","sequential / link")
    node(ax,.45,1.5,2.05,1.8,"Branch + next PC","PC, imm, rs1, rs2,\nALU result + controls",TEAL)
    route(ax,[(2.5,8.83),(3.2,8.83)],"PC",(2.85,9.1))
    route(ax,[(5.6,8.83),(6.3,8.83)],"instruction",(5.95,9.62))
    route(ax,[(4.4,8.4),(4.4,5.8)],"rs1 / rs2 / rd",(4.4,7.1))
    route(ax,[(5.6,8.56),(5.93,8.56),(5.93,7.05),(6.3,7.05)])
    route(ax,[(7.5,6.55),(7.5,5.8)],"immediate",(8.22,6.2))
    route(ax,[(5.6,5.13),(6.3,5.13)],"rs1 / rs2",(5.95,5.48))
    route(ax,[(8.75,5.13),(9.8,5.13)],"A / B",(9.27,5.43))
    route(ax,[(11.4,4.5),(11.4,3.0)],"address",(12.12,3.75))
    route(ax,[(10.45,4.5),(10.45,3.77),(5.02,3.77),(5.02,3.0)],"ALU result",(7.35,3.77))
    route(ax,[(5.6,4.7),(5.96,4.7),(5.96,3.32),(13.25,3.32),(13.25,2.3),(12.7,2.3)],
          "rs2: store data",(9.03,3.32))
    route(ax,[(9.65,2.25),(8.75,2.25)],"word",(9.2,2.57))
    route(ax,[(6.3,2.25),(5.6,2.25)],"load",(5.94,2.6))
    route(ax,[(4.4,3.0),(4.4,4.45)],"rd data",(4.4,3.47),TEAL)
    route(ax,[(1.48,8.4),(1.48,7.3)])
    route(ax,[(1.7,6.45),(2.88,6.45),(2.88,.83),(4.4,.83),(4.4,1.5)],
          "PC+4",(3.8,.83),TEAL)
    route(ax,[(1.2,6.45),(1.2,3.3)],"PC+4",(1.2,4.76),TEAL)
    route(ax,[(.45,2.35),(.12,2.35),(.12,8.8),(.45,8.8)],
          "next PC",(.12,5.64),TEAL)
    route(ax,[(3.2,5.2),(2.68,5.2),(2.68,2.35),(2.5,2.35)],
          "rs1 / rs2",(2.75,4.06),TEAL)
    route(ax,[(8.75,8.85),(9.22,8.85),(9.22,6.01),(8.42,6.01),(8.42,5.8)],
          "controls",(10.0,7.24),GRAY,True)
    ax.text(6.3,9.89,"SINGLE-CYCLE DATAPATH",fontweight="bold",fontsize=15,color=NAVY,ha="center")
    ax.text(6.8,.35,"Named PC/immediate/ALU inputs to next-PC logic are expanded in the separate next-PC diagram.",
            fontsize=8.1,color=GRAY,ha="center")
    save_diagram(fig,"block_diagram")

    fig,ax=plt.subplots(figsize=(11.6,6.2)); ax.set_xlim(0,12); ax.set_ylim(.1,6.9); ax.axis("off")
    node(ax,.25,5.4,2.8,.8,"PC + 4","default next PC")
    node(ax,.25,3.65,2.8,.95,"PC + immediate","B / J offset")
    node(ax,.25,1.9,2.8,1.0,"(rs1 + imm) & ~1","JALR target")
    node(ax,4.5,3.4,2.3,2.0,"Next-PC MUX","JALR > JAL/branch\n> sequential",TEAL)
    node(ax,8.4,4.0,2.7,.9,"PC register","enabled rising edge",TEAL)
    node(ax,4.45,.35,3.6,1.15,"Branch comparator","rs1 vs rs2: EQ/NE/LT/GE/LTU/GEU")
    node(ax,8.4,1.85,2.7,1.0,"Trap guard","reject target[1:0] != 0")
    route(ax,[(3.05,5.8),(3.85,5.8),(3.85,4.95),(4.5,4.95)])
    route(ax,[(3.05,4.13),(4.5,4.13)])
    route(ax,[(3.05,2.4),(3.85,2.4),(3.85,3.75),(4.5,3.75)])
    route(ax,[(6.8,4.45),(8.4,4.45)],"next_pc",(7.6,4.76),TEAL)
    route(ax,[(5.6,1.5),(5.6,3.4)],"branch_taken",(5.6,2.35),TEAL)
    route(ax,[(6.8,4.05),(7.6,4.05),(7.6,2.35),(8.4,2.35)],"taken target",(7.7,3.08),TEAL)
    route(ax,[(9.75,2.85),(9.75,4.0)],"hold / halt",(10.57,3.43),GRAY,True)
    ax.text(6,6.63,"CONTROL-FLOW PATH",fontweight="bold",fontsize=15,color=NAVY,ha="center")
    save_diagram(fig,"next_pc")

    fig,ax=plt.subplots(figsize=(12,5.8)); ax.set_xlim(0,12.5); ax.set_ylim(0,6.1); ax.axis("off")
    node(ax,.15,2.5,2.2,1.1,"Assembly","52 .S sources")
    node(ax,3.1,2.5,2.25,1.1,"Project assembler","32-bit words")
    node(ax,6.05,4.35,2.65,1.0,"RTL + testbench","actual trace/state")
    node(ax,6.05,1.5,2.65,1.0,"Python ISA model","golden trace/state")
    node(ax,9.6,2.35,2.55,1.35,"Comparator","retire / regs / memory\ntrap / halt",TEAL)
    node(ax,3.1,.1,2.65,1.0,"GNU assembler","independent word match")
    route(ax,[(2.35,3.05),(3.1,3.05)])
    route(ax,[(5.35,3.05),(5.65,3.05),(5.65,4.85),(6.05,4.85)])
    route(ax,[(5.35,3.05),(5.65,3.05),(5.65,2),(6.05,2)])
    route(ax,[(8.7,4.85),(9.05,4.85),(9.05,3.35),(9.6,3.35)],color=TEAL)
    route(ax,[(8.7,2),(9.05,2),(9.05,2.75),(9.6,2.75)],color=TEAL)
    route(ax,[(1.25,2.5),(1.25,.65),(3.1,.65)])
    route(ax,[(4.42,1.1),(4.42,2.5)],"52 matches",(4.42,1.75),GRAY,True)
    ax.text(6.2,5.77,"VERIFICATION FLOW",fontweight="bold",fontsize=15,color=NAVY,ha="center")
    save_diagram(fig,"verification_flow")

    bc=summary["branch_coverage"]; names=["BEQ","BNE","BLT","BGE","BLTU","BGEU"]
    fig,ax=plt.subplots(figsize=(9.2,3.4))
    t=[bc[n+"_TAKEN"] for n in names]; nt=[bc[n+"_NOT_TAKEN"] for n in names]
    ax.barh(names,t,color=TEAL,label="Taken"); ax.barh(names,nt,left=t,color=BLUE,label="Not taken")
    ax.invert_yaxis(); ax.spines[["top","right"]].set_visible(False)
    ax.set_xlabel("Successfully retired branch events"); ax.legend(loc="lower right",frameon=False)
    ax.tick_params(labelsize=10); ax.grid(axis="x",alpha=.16); ax.set_axisbelow(True)
    fig.tight_layout(); save_diagram(fig,"branch_coverage")

def fonts():
    candidates=[Path("/usr/share/fonts/truetype/dejavu"),Path("C:/Windows/Fonts")]
    base=next((p for p in candidates if (p/"DejaVuSans.ttf").exists()),None)
    if base:
        for name,file in (("Body","DejaVuSans.ttf"),("BodyBold","DejaVuSans-Bold.ttf"),("Mono","DejaVuSansMono.ttf")):
            pdfmetrics.registerFont(TTFont(name,str(base/file)))
    else:
        for name,target in (("Body","Helvetica"),("BodyBold","Helvetica-Bold"),("Mono","Courier")):
            pdfmetrics.registerFont(pdfmetrics.Font(name,target,"WinAnsiEncoding"))

def report(summary,synth,gnu,manifest):
    fonts(); styles=getSampleStyleSheet()
    styles.add(ParagraphStyle("BodyTextCustom",fontName="Body",fontSize=9.8,leading=14.2,textColor=HexColor(NAVY),spaceAfter=7))
    styles.add(ParagraphStyle("SmallCustom",fontName="Body",fontSize=8.2,leading=11.5,textColor=HexColor(GRAY),spaceAfter=5))
    styles.add(ParagraphStyle("TitleCustom",fontName="BodyBold",fontSize=24,leading=29,textColor=HexColor(NAVY),spaceAfter=15))
    styles.add(ParagraphStyle("SubCustom",fontName="BodyBold",fontSize=12,leading=16,textColor=HexColor(TEAL),spaceBefore=8,spaceAfter=7))
    styles.add(ParagraphStyle("KickerCustom",fontName="BodyBold",fontSize=8.5,leading=12,textColor=HexColor(TEAL),spaceAfter=8))
    styles.add(ParagraphStyle("CellCustom",fontName="Body",fontSize=8.6,leading=12,textColor=HexColor(NAVY)))
    styles.add(ParagraphStyle("CellHeadCustom",fontName="BodyBold",fontSize=8.7,leading=12,textColor=white))
    styles.add(ParagraphStyle("CodeCustom",fontName="Mono",fontSize=7.6,leading=11,textColor=HexColor(NAVY),backColor=HexColor(LIGHT),borderPadding=10,spaceBefore=5,spaceAfter=10))
    styles.add(ParagraphStyle("MetricCustom",fontName="BodyBold",fontSize=25,leading=32,textColor=HexColor(NAVY)))
    story=[]; width=A4[0]-96

    def rich(text):
        pieces=text.split(chr(96))
        return "".join(escape(t) if i%2==0 else '<font name="Mono">'+escape(t)+'</font>' for i,t in enumerate(pieces))
    def p(text,small=False):
        story.append(Paragraph(rich(text),styles["SmallCustom" if small else "BodyTextCustom"]))
    def sub(text): story.append(Paragraph(escape(text),styles["SubCustom"]))
    def code(text): story.append(Preformatted(text.strip("\n"),styles["CodeCustom"]))
    def table(rows,col_widths):
        content=[]
        for i,row in enumerate(rows):
            content.append([Paragraph(rich(str(v)),styles["CellHeadCustom" if i==0 else "CellCustom"]) for v in row])
        t=Table(content,colWidths=col_widths,repeatRows=1,hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),HexColor(NAVY)),("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LEFTPADDING",(0,0),(-1,-1),9),("RIGHTPADDING",(0,0),(-1,-1),9),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[HexColor("#F0F5F8"),white]),
            ("LINEBELOW",(0,-1),(-1,-1),.5,HexColor("#C9D8E3"))]))
        story.extend([t,Spacer(1,9)])
    def image(name,h=None):
        obj=Image(str(DOCS/(name+".png")))
        ratio=obj.imageHeight/obj.imageWidth; obj.drawWidth=width; obj.drawHeight=width*ratio
        if h and obj.drawHeight>h: obj.drawHeight=h; obj.drawWidth=h/ratio
        obj.hAlign="CENTER"; story.extend([obj,Spacer(1,8)])
    def page(n,title,subtitle):
        if story: story.append(PageBreak())
        story.append(Paragraph(f"{n:02d} / DESIGN AND VERIFICATION",styles["KickerCustom"]))
        story.append(Paragraph(escape(title),styles["TitleCustom"])); p(subtitle)

    story.append(Spacer(1,42))
    story.append(Paragraph("PROJECT PACKAGE / VERSION 1.0",styles["KickerCustom"]))
    story.append(Paragraph('<font name="BodyBold" size="59" color="'+NAVY+'">RV32I</font>',
                           ParagraphStyle("CoverBig",fontName="BodyBold",fontSize=59,leading=67,spaceAfter=15)))
    story.append(Paragraph("Single-Cycle Processor",styles["TitleCustom"]))
    story.append(Paragraph("RTL, simulation and verification",styles["SubCustom"]))
    p("A modular implementation with checked instruction traces, byte-accurate memory operations and a reproducible Vivado workflow.")
    story.append(Spacer(1,23))
    metrics=Table([[Paragraph("37",styles["MetricCustom"]),
                    Paragraph("52",styles["MetricCustom"]),
                    Paragraph("12,604",styles["MetricCustom"])],
                   [Paragraph("Datapath instructions",styles["SmallCustom"]),Paragraph("Test programs",styles["SmallCustom"]),
                    Paragraph("Retirement checks",styles["SmallCustom"])]],colWidths=[width/3]*3)
    metrics.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),HexColor(LIGHT)),("TOPPADDING",(0,0),(-1,0),20),
                                ("BOTTOMPADDING",(0,1),(-1,1),14),("LEFTPADDING",(0,0),(-1,-1),14)]))
    story.append(metrics); story.append(Spacer(1,22))
    sub("Included")
    p("Nine Verilog RTL modules; six self-checking SystemVerilog testbenches; directed and seeded programs; an independent Python architectural model; editable block diagrams; Vivado scripts; actual verification logs.")
    sub("Evidence status")
    p("Icarus simulation, GNU assembler comparison and Yosys generic synthesis were executed successfully. Vivado/XSim and FPGA hardware execution remain for local reproduction.")
    p("Prepared 09 October 2026. New implementation inspired by the linked learning repository; attribution and primary references appear on page 16.",True)

    page(2,"Scope and architecture","The design follows the RV32I base integer instruction behavior in a deliberately small execution environment.")
    table([
        ["Family","Instructions","Count"],
        ["Register arithmetic","ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND","10"],
        ["Immediate arithmetic","ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI","9"],
        ["Loads","LB, LH, LW, LBU, LHU","5"],
        ["Stores","SB, SH, SW","3"],
        ["Conditional branches","BEQ, BNE, BLT, BGE, BLTU, BGEU","6"],
        ["Upper immediates","LUI, AUIPC","2"],
        ["Unconditional jumps","JAL, JALR","2"],
    ],[125,319,55])
    sub("Three additional instruction groups")
    p("FENCE is a no-op because the supplied memories are strongly ordered and there is one hart. ECALL and EBREAK stop execution with metadata. These bring the exercised mnemonic bins to 40; they do not add datapath arithmetic operations.")
    sub("Machine model")
    p("32 registers, 32-bit addresses and data, little-endian memory and fixed 32-bit instructions. Instructions and data have separate 4 KiB spaces in the simulation wrapper. One instruction can complete on each clock edge after reset, provided the combinational memory contract is met.")
    sub("Boundary of the project")
    p("There is no pipeline, cache, memory handshake, privileged state, CSR file, interrupt path, M/C/A extension or FENCE.I. Traps halt rather than enter a software handler. This is an educational implementation, not a certified RISC-V processor or an OS-ready system.")

    page(3,"The datapath","Follow the blue data paths first. The teal paths carry writeback and control flow; the decoder supplies control selections.")
    image("block_diagram",365)
    table([
        ["Step","What happens"],
        ["Fetch","PC selects a word in instruction memory."],
        ["Decode / read","Instruction fields select two GPRs; the decoder and immediate generator interpret the instruction."],
        ["Execute / memory","Operand MUXes feed the ALU; branches compare GPRs; loads/stores use the ALU address."],
        ["Complete","Writeback selects ALU, load data or PC+4. At the edge, state changes or a trap is latched."],
    ],[103,396])
    p("The next-PC block includes comparison and target selection; its named PC/immediate/ALU inputs are expanded on the next page. Fault checking gates PC, register and store updates.",True)

    page(4,"PC, branches and jumps","The value written to a register and the next instruction address are separate choices.")
    image("next_pc",282)
    table([
        ["Instruction","Next PC","Register writeback"],
        ["Normal / untaken branch","PC + 4","Instruction-dependent"],
        ["Taken branch","PC + B immediate","None"],
        ["JAL","PC + J immediate","rd = PC + 4"],
        ["JALR","(rs1 + I immediate) & ~1","rd = PC + 4"],
    ],[135,198,166])
    sub("Why PC+4 is a third writeback input")
    p("A jump stores the address of the following instruction as a return link. The improved core therefore has three writeback sources: ALU result, extended load data and PC+4. JAL with rd=x0 performs a jump without changing a register.")
    p("JALR clears bit 0, then the core checks four-byte instruction alignment because compressed instructions are not supported. Only a taken branch's target is checked for misalignment.")

    page(5,"Single-cycle timing","Combinational results become available during a cycle. Register-file storage changes at the next rising edge.")
    table([
        ["Moment","Processor activity"],
        ["Rising edge N","PC and any previous instruction's architectural updates take effect."],
        ["Between N and N+1","Fetch, decode, GPR read, ALU, optional data read and writeback selection settle."],
        ["Rising edge N+1","Write the destination GPR, commit store bytes and update PC; register the retirement event."],
    ],[138,361])
    sub("ADD example")
    code("add x3, x1, x2\nALU A = x1, ALU B = x2\nwriteback_data = ALU result\nx3 changes on the next rising edge, not immediately after the ALU.")
    sub("LW example")
    code("lw x3, 8(x1)\naddress = x1 + 8\ncombinational data-memory word -> load extension -> writeback\nx3 changes on the same completion edge as the PC update.")
    sub("Memory choice matters")
    p("A synchronous-read RAM would return the load word after the edge at which this core expects to write the register. The supplied memory uses asynchronous reads and rising-edge stores, so the LW path remains single-cycle.")
    p("On an FPGA, this implies distributed memory or registers. Replacing it with block RAM requires a multi-cycle or pipelined design with suitable control. The longest path often includes instruction fetch, decode, ALU and load read; a slower clock may be necessary.")
    sub("Reading a waveform")
    p("After an edge, trace_pc describes the instruction that completed; the live PC normally describes the next one. Always qualify registered trace fields with retire_valid.")

    page(6,"RTL module map","The source files are small enough to study one at a time. Integration lives in rv32i_core.v.")
    table([
        ["File","Responsibility"],
        ["rv32i_pc.v","Enabled, synchronous PC register; parameterized reset address."],
        ["rv32i_regfile.v","32 x 32-bit GPRs; two reads, debug read, one edge-timed write; x0 protection."],
        ["rv32i_immediate.v","I/S/B/U/J extraction and sign extension."],
        ["rv32i_decoder.v","Opcode/funct3/funct7 validation; shared control encodings; illegal-instruction default."],
        ["rv32i_alu.v","Ten complete combinational operations and a continuously assigned zero flag."],
        ["rv32i_branch.v","Six direct signed/unsigned comparisons."],
        ["rv32i_core.v","Operand and writeback MUXes, byte lanes, next-PC logic, faults and retirement trace."],
        ["rv32i_memory.v","Independent asynchronous instruction/data reads; masked stores; bounds checking."],
        ["rv32i_system.v","Convenience core + memory wrapper for simulation."],
    ],[151,348])
    sub("One source of control encodings")
    p("rv32i_defs.vh defines every internal ALU, immediate, branch and MUX code. Both decoding and datapath logic include it, preventing the original decoder/ALU mismatch.")
    sub("Top modules")
    p("tb_system is the full-processor simulation top. rv32i_core is the synthesis top, with external memory interfaces. Synthesizing a fixed demo ROM together with the CPU can let tools remove logic that the program never uses.")

    page(7,"Decode and immediate generation","The decoder selects a behavior only when the relevant instruction fields are legal.")
    table([
        ["Format","Immediate reconstructed by RTL"],
        ["I","Sign-extend instruction[31:20]."],
        ["S","Sign-extend {instruction[31:25], instruction[11:7]}."],
        ["B","{sign, bit 7, bits 30:25, bits 11:8, 0}, then sign-extend."],
        ["U","instruction[31:12] followed by 12 zero bits."],
        ["J","{sign, bits 19:12, bit 20, bits 30:21, 0}, then sign-extend."],
    ],[69,430])
    sub("Control examples")
    table([
        ["Instruction","ALU inputs","Writeback","Other controls"],
        ["ADD","rs1, rs2","ALU","Register write"],
        ["ADDI","rs1, I imm","ALU","Register write"],
        ["LW","rs1, I imm","Load","Memory read; size=word"],
        ["SW","rs1, S imm","None","Memory write; size=word"],
        ["LUI","0, U imm","ALU","Register write"],
        ["AUIPC","PC, U imm","ALU","Register write"],
        ["JAL","Unused","PC+4","PC + J immediate"],
        ["JALR","rs1, I imm","PC+4","Masked ALU target"],
    ],[78,121,77,223])
    p("Negative ADDI values must still select ADD: instruction bit 30 belongs to the immediate and is not a SUB selector. Shift-immediate instructions instead validate their high encoding bits. Unsupported funct7 values, widths and opcodes are illegal.",True)

    page(8,"ALU and branch decisions","All combinational blocks assign every output. Signed and unsigned comparisons are intentional choices.")
    table([
        ["Operation","Code","Meaning"],
        ["ADD / SUB","0 / 1","32-bit addition/subtraction; overflow wraps modulo 2^32."],
        ["AND / OR / XOR","2 / 3 / 4","Bitwise operations."],
        ["SLL / SRL / SRA","5 / 6 / 7","Shift by b[4:0]; SRA treats a as signed."],
        ["SLT / SLTU","8 / 9","Result is 1 or 0 using signed/unsigned ordering."],
    ],[148,71,280])
    sub("A complete combinational ALU")
    code("always @* begin\n    case (operation)\n        `ALU_ADD: result = a + b;\n        `ALU_SRA: result = $signed(a) >>> b[4:0];\n        // Other operations are in rv32i_alu.v.\n        default:  result = 32'b0;\n    endcase\nend\nassign zero = (result == 32'b0);")
    p("The continuous zero assignment avoids retaining a previous flag value. Invalid ALU codes produce zero; the instruction decoder separately rejects invalid instructions.")
    sub("Branches do not rely on subtraction's sign")
    p("The branch unit compares rs1_data and rs2_data directly. For example, INT_MIN is less than INT_MAX as signed integers, even though their 32-bit difference can wrap and have the wrong sign for a naive subtraction-based comparison.")
    table([
        ["Comparison","Signed interpretation","Unsigned interpretation"],
        ["0xFFFFFFFF vs 0x00000001","-1 < 1: true","4,294,967,295 < 1: false"],
        ["Branch operations","BLT / BGE","BLTU / BGEU"],
    ],[184,157,158])

    page(9,"Byte and halfword memory operations","The ALU produces a byte address. The memory returns an aligned word; the core selects and extends the requested lane.")
    sub("Example word at address 0x200")
    p("Store 0x80FF7F01. Little-endian bytes at 0x200..0x203 are 01, 7F, FF, 80.")
    table([
        ["Load","Value written to rd","Why"],
        ["LB at 0x203","0xFFFFFF80","Sign-extend byte 0x80."],
        ["LBU at 0x203","0x00000080","Zero-extend byte 0x80."],
        ["LH at 0x202","0xFFFF80FF","Sign-extend halfword 0x80FF."],
        ["LHU at 0x202","0x000080FF","Zero-extend halfword 0x80FF."],
        ["LW at 0x200","0x80FF7F01","Full aligned word."],
    ],[121,147,231])
    sub("Stores preserve neighboring bytes")
    table([
        ["Store","Strobes [3:0]","Bus operation"],
        ["SB, address offset 0","0001","Write only lane 0."],
        ["SB, address offset 3","1000","Shift low byte left by 24 bits."],
        ["SH, address offset 2","1100","Shift low halfword left by 16 bits."],
        ["SW, aligned","1111","Write all four bytes."],
    ],[151,105,243])
    code("shifted_load = dmem_read_data >> (8 * address[1:0]);\nstore_data   = rs2_data       << (8 * address[1:0]);")
    p("Halfwords require two-byte alignment; words require four-byte alignment. Bounds checking uses the requested access width and does not wrap a large address into the RAM array. Faults force store strobes to zero.")

    page(10,"Faults, halt and reset","A faulting instruction must not partly modify architectural state.")
    table([
        ["Cause","Event","Recorded value"],
        ["0","Instruction address misaligned","PC or taken target"],
        ["1","Instruction access fault","Fetch address"],
        ["2","Illegal instruction","Instruction word"],
        ["3","EBREAK","0"],
        ["4 / 5","Load misalignment / access fault","Effective address"],
        ["6 / 7","Store misalignment / access fault","Effective address"],
        ["11","ECALL","0"],
    ],[57,244,198])
    sub("Atomic stop behavior")
    p("Fault detection disables PC update, GPR write and all store lanes. On the edge, halted becomes 1 and cause/PC/value are recorded. No retire event is produced for the faulting instruction. The state stays stable until synchronous reset.")
    p("A load to x0 still performs memory access checks. An inaccessible aligned jump target faults on the next fetch; a misaligned target faults at the branch/jump itself. An untaken branch does not inspect its unused target.")
    sub("Reset contract")
    p("Active-high synchronous reset sets PC to RESET_PC, clears every GPR and clears halt/trap/trace state. It takes effect at a rising edge. The data memory has no reset input and retains its contents; testbenches clear it explicitly between cases.")
    sub("Execution-environment limit")
    p("The numeric causes follow common RISC-V conventions, but they are debug outputs rather than CSRs. Cause 11 is used for ECALL; there is no implemented machine-mode state, trap vector, handler or MRET.")
    p("Fault priority is defined in docs/Interface_Contract.md and enforced by both the core and reference model.",True)

    page(11,"Verification strategy","Waveforms help explain behavior; self-checking tests establish whether the expected result was produced.")
    image("verification_flow",238)
    sub("Three levels of checks")
    p("1. Component benches validate arithmetic, immediates, decode legality, register timing and memory lanes.")
    p("2. Processor regression compares every successful instruction event with a Python architectural oracle, then checks all 32 registers and all 4096 memory bytes.")
    p("3. Trap metadata, fault-side-effect suppression, halted-state stability and reset are checked separately.")
    sub("What an event contains")
    p("PC, instruction, next PC, GPR write flag/index/value, load flag, memory address, store strobes and shifted store data. Records use ten 32-bit fields; stores are also validated through final byte-addressed memory.")
    sub("Independent checks and their limits")
    p("The Python interpreter does not import RTL control codes and updates individual memory bytes. GNU binutils independently matched all program encodings. Yosys checked the core structurally and rejected inferred latches.")
    p("The oracle is custom project software. This regression is not a formal proof, official compliance suite or exhaustive test of every legal program.",True)

    page(12,"Measured verification results","The numbers below come from included logs and JSON summaries, not planned runs.")
    table([
        ["Check","Actual result"],
        ["Icarus Verilog","Version 12.0; all six testbenches PASS."],
        ["ALU / branch","13,752 checks."],
        ["Immediate / register file","8,192 / 98 checks."],
        ["Decoder / memory","2,093 / 13 checks."],
        ["Processor regression","52 programs; 12,604 successful events."],
        ["Random generation","16 fixed seeds; 400 generation blocks per program."],
        ["Final state / traps","All GPRs, full 4 KiB data RAM and trap metadata per case."],
        ["Mnemonic / branch bins","40/40 exercised; 12/12 branch outcomes."],
        ["GNU word comparison","52/52 exact image matches."],
        ["Yosys generic synthesis","PASS; zero inferred latches; no structural errors."],
    ],[161,338])
    image("branch_coverage",184)
    p("The chart counts successfully retired branches. Faulting branches and ECALL/EBREAK are checked through trap tests. Functional bins are not code/toggle coverage. See results/verified/ for original logs, CSV, VCD, source hashes and summaries.",True)

    page(13,"Programs you can demonstrate","The examples exercise dependencies, loops and memory updates, not only isolated ALU operations.")
    table([
        ["Program","Behavior","Retired"],
        ["directed_isa","All instruction families, signed corners, byte lanes, all branch outcomes and jump links.","94"],
        ["fibonacci","Write F0..F11 at byte addresses 128..175.","88"],
        ["bubble_sort","Sort nine signed integers at addresses 256..291.","315"],
        ["random_00..15","Seeded instruction blocks with bounded loops, branches, subword memory and jumps.","12,089 total"],
    ],[121,303,75])
    sub("Fibonacci output")
    code("Address 0x080 onwards, one 32-bit word each:\n0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89")
    sub("Signed bubble sort")
    code("Input : 23, -7, 0, 99, -100, 23, 1, 2147483647, -2147483648\nOutput: -2147483648, -100, -7, 0, 1, 23, 23, 99, 2147483647")
    p("Bubble sort stores a completion flag of 1 at data address 0. Successful examples stop on EBREAK; this is the expected execution-environment stop, not a test failure.")
    sub("Fault and boundary tests")
    p("33 additional programs cover illegal encodings, unsupported CSR/FENCE.I, ECALL, instruction/data access faults, alignment faults, load-to-x0 behavior and taken versus untaken misaligned branch targets.")
    sub("Adding a case")
    p("Add a program in tools/build_programs.py, regenerate vectors and rerun the regression. Keep bounded execution and use EBREAK to finish normal tests. Inspect mismatches rather than changing golden data to match incorrect RTL.")

    page(14,"Run it in Vivado","The supplied vectors are committed, so the Vivado regression does not require Python.")
    sub("GUI: first successful run")
    p("Extract the whole ZIP to a writable, short path. Open a new Vivado GUI session. Replace the example path below with your extracted folder.")
    code("source {C:/RISC_V/RV32I_Single_Cycle_Project/scripts/vivado/create_project.tcl}\nlaunch_simulation\nrun all")
    p("The default part is xc7z020clg400-1. Set RV32I_PART to another installed part before sourcing the script if needed.")
    sub("Required pass messages")
    code("SYSTEM_SUMMARY cases=52 retired=12604\nTESTBENCH_PASS tb_system")
    p("A failure stops with $fatal. The PASS file and retire CSV appear in results/user_runs/xsim/. Batch mode deletes old pass markers before each testbench.")
    sub("All six testbenches")
    code("vivado -mode batch -source scripts/vivado/run_regression.tcl\n# Require: VIVADO_REGRESSION_PASS")
    sub("Waveform study")
    p("Expand tb_system/dut/u_core. Start with pc, instruction, rs1_data, rs2_data, immediate, alu_a, alu_b, alu_result and writeback_data. Add register_write_enable, next_pc and branch_taken; then memory signals and registered trace fields.")
    p("Use hexadecimal for instructions/addresses/data. After a rising edge, live PC normally points to the next instruction, while trace_pc identifies the completed one.")
    p("Vivado/XSim was not executed during preparation. These scripts are reproduction entry points; keep your local logs and screenshots. Detailed guidance and troubleshooting are in docs/Vivado_Guide.md.",True)

    page(15,"Synthesis and engineering choices","A frequency constraint is a target; a measured implementation needs its own evidence.")
    sub("Run core-only Vivado synthesis")
    code("vivado -mode batch -source scripts/vivado/run_synthesis.tcl")
    p("The script emits utilization, timing-summary and methodology reports plus a synthesized checkpoint in results/user_runs/vivado_synthesis/. The top is rv32i_core with external memory ports; debug and retirement circuitry contribute to area.")
    sub("Actual generic synthesis result")
    p("Yosys generic synthesis completed with 7,981 mapped logic cells and zero inferred latches. This cell count is not an FPGA LUT/FF utilization count. It includes the register file and observation logic; simulation memories are outside the synthesis top.")
    sub("The 10 ns constraint")
    p("core_clock.xdc specifies a 10 ns target. No external-memory I/O delays, board pins, placement, routing or bitstream are supplied. Synthesis estimates alone cannot establish board timing closure or a maximum operating frequency.")
    sub("Corrections relative to the learning reference")
    table([
        ["Issue identified","Implementation in this package"],
        ["ALU decoder/datapath mismatch","Shared definitions; all operations tested."],
        ["Incomplete zero-flag assignments","Continuous zero assignment; complete combinational defaults."],
        ["Clocked read in a single-cycle load path","Combinational memory-read contract."],
        ["Ambiguous PC+4 writeback diagram","Explicit third writeback input for JAL/JALR."],
        ["Limited / inconsistent testbench hookup","Six self-checking benches plus architectural trace comparison."],
    ],[178,321])
    p("Original repository commit inspected: 577eb7e10d091069c6b1e67968ad49eca284749c. The new package does not redistribute its RTL or report.",True)

    page(16,"Review, resume and next steps","Use the package as a learning project, then collect evidence from your own runs.")
    sub("Before putting it on your resume")
    p("Explain ADD, LW, SW and JALR through the block diagram. Reproduce all Vivado tests. Make one controlled RTL change, predict the effect and demonstrate that the checker catches the resulting mismatch. Keep your new logs and screenshots.")
    sub("Suggested project description")
    p("Implemented a modular 32-bit single-cycle RISC-V core with 37 RV32I datapath instructions, subword memory operations and fault reporting; developed six self-checking testbenches and checked 52 programs / 12,604 instruction events against an architectural reference flow.")
    p("Use this wording only after reviewing and reproducing the work. Add Vivado metrics only after local runs. The project is not UVM, formally verified, OS-capable or board-demonstrated.")
    sub("Expand it in stages")
    table([
        ["Stage","Next engineering task"],
        ["1","Reproduce XSim and core synthesis; explain the measured results."],
        ["2","Add independent Spike/Sail or architectural-test checks."],
        ["3","Introduce a memory handshake and synchronous block RAM."],
        ["4","Pipeline the core; add forwarding, stalls and branch flush tests."],
        ["5","Build a small system with peripherals and documented CSR/trap support."],
    ],[54,445])
    sub("References and attribution")
    refs=[
        ("RISC-V International - RV32I Base Integer Instruction Set, version 2.1",
         "https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html"),
        ("AMD - UG900, Vivado Design Suite User Guide: Logic Simulation (2022.1)",
         "https://www.amd.com/content/dam/xilinx/support/documents/sw_manuals/xilinx2022_1/ug900-vivado-logic-simulation.pdf"),
        ("AMD - UG835, launch_simulation Tcl command",
         "https://docs.amd.com/r/2021.1-English/ug835-vivado-tcl-commands/launch_simulation"),
        ("Learning reference - Samad Abbasi, RISC-V-Single-Cycle-Processor",
         "https://github.com/samad-abbasi/RISC-V-Single-Cycle-Processor")
    ]
    for title,url in refs:
        story.append(Paragraph('<link href="'+escape(url)+'" color="'+BLUE+'">'+escape(title)+'</link>',styles["SmallCustom"]))
    p("Supporting evidence and commands are included with the source. The implementation and tests are newly written for this package.",True)

    def decorate(c,doc):
        c.saveState(); c.setStrokeColor(HexColor("#D5E0E8")); c.setLineWidth(.5)
        c.line(48,A4[1]-34,A4[0]-48,A4[1]-34)
        c.setFont("BodyBold",7.2); c.setFillColor(HexColor(GRAY))
        c.drawString(48,A4[1]-25,"RV32I / DESIGN + VERIFICATION")
        c.setFont("Body",7.2); c.drawString(48,24,"Single-Cycle Processor Project  |  v1.0")
        c.drawRightString(A4[0]-48,24,f"{doc.page:02d}"); c.restoreState()
    path=DOCS/"Design_and_Verification_Report.pdf"
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=54,bottomMargin=43,
                          title="RV32I Single-Cycle Processor - Design and Verification",author="RV32I Project Package",
                          subject="RTL architecture, verified regression and Vivado reproduction workflow")
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    if doc.page!=16: raise RuntimeError(f"Expected 16 report pages, got {doc.page}; inspect page overflow")
    print(f"Generated {path.name}: {doc.page} pages.")

def main():
    summary=json.loads((ROOT/"results/verified/iverilog/verification_summary.json").read_text())
    synth=json.loads((ROOT/"results/verified/yosys/synthesis_summary.json").read_text())
    gnu=json.loads((ROOT/"results/verified/gnu/gnu_assembler_check.json").read_text())
    manifest=json.loads((ROOT/"programs/generated/manifest.json").read_text())
    assert summary["status"]==synth["status"]==gnu["status"]=="PASS"
    assert (summary["cases_passed"],summary["retired_events_checked"])==(52,12604)
    diagrams(summary); report(summary,synth,gnu,manifest)
if __name__=="__main__": main()

