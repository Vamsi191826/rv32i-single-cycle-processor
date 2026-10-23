# RV32I Single-Cycle Processor and Verification Project

An educational, modular 32-bit RISC-V core with a reproducible verification flow. Start with [START_HERE.md](START_HERE.md). The design report and editable engineering diagrams are in `docs/`.

## Design scope

| Feature | Implementation |
| --- | --- |
| Integer arithmetic | ADD, SUB, AND, OR, XOR, shifts, signed/unsigned set-less-than; immediate variants |
| Control flow | BEQ/BNE/BLT/BGE/BLTU/BGEU, JAL, JALR with bit 0 cleared |
| Upper immediates | LUI, AUIPC |
| Memory | LB/LH/LW/LBU/LHU, SB/SH/SW, little endian, byte write strobes |
| Architectural registers | 32 x 32-bit; x0 protected; two asynchronous reads, one rising-edge write |
| Normal instructions | 37 datapath instructions plus FENCE as a no-op |
| Execution environment | ECALL/EBREAK and faults halt with cause, PC and value; reset resumes |
| Observability | Registered retirement trace and an asynchronous debug register port |
| Simulation memory | Separate 4 KiB instruction and 4 KiB data spaces, combinational reads, clocked stores |

This implements the RV32I instruction behavior for a minimal execution environment. It is not an officially certified RISC-V implementation. There is no privileged ISA, CSR file, trap vector, interrupt controller, M/C/A extension, cache, AXI interface or stall protocol. FENCE.I is illegal. ECALL/EBREAK do not retire.

## Repository map

| Folder/file | Purpose |
| --- | --- |
| `rtl/*.v` | Nine Verilog modules; `rv32i_defs.vh` shares control encodings |
| `tb/*.sv` | Six classless, self-checking SystemVerilog testbenches |
| `tb/generated/case_list.svh` | 52 committed test cases; Vivado does not need Python |
| `programs/*.S` | Directed tests, Fibonacci, signed bubble sort, seeded stress and fault programs |
| `programs/generated/` | Program words, independent golden traces, final register/memory files, manifest |
| `tools/` | Small assembler, architectural model, program generator, simulator runner, synthesis/check tools |
| `scripts/vivado/` | Project creation, all-testbench regression and core synthesis |
| `constraints/core_clock.xdc` | 10 ns target clock; no board pins or external-memory I/O timing assumptions |
| `docs/` | PDF report, block diagrams, interface and verification notes |
| `results/verified/` | Actual Icarus/GNU/Yosys evidence supplied with this package |
| `results/user_runs/` | Your fresh Vivado or portable-tool output |

RTL uses Verilog-2001. Testbenches use SystemVerilog for strings, tasks and assertions; they are not UVM testbenches.

## Vivado

Use a new GUI session, then source `scripts/vivado/create_project.tcl`, run `launch_simulation` and `run all`. Detailed commands, expected output and waveform guidance are in [docs/Vivado_Guide.md](docs/Vivado_Guide.md).

From a terminal with Vivado on PATH:

```sh
vivado -mode batch -source scripts/vivado/run_regression.tcl
vivado -mode batch -source scripts/vivado/run_synthesis.tcl
```

Default part: `xc7z020clg400-1`. Set environment variable `RV32I_PART` to another installed FPGA part if needed. Scripts create or replace the generated `build/vivado/` project. Synthesis top is `rv32i_core`; simulation top is `tb_system`.

The 10 ns constraint is a design target. No Vivado run, routed timing closure, Fmax, resource count or board demonstration is claimed.

## Portable simulation

Install Python 3.9+ and Icarus Verilog with SystemVerilog support:

```sh
python3 tools/run_regression.py
python3 tools/run_regression.py --waves
```

The second command creates `results/user_runs/iverilog/system.vcd`, viewable in GTKWave. The runner uses argument lists, fresh PASS markers, a process timeout and a second CSV trace check.

Vivado command-line tools can also run the same benches:

```sh
python3 tools/run_regression.py --simulator xsim
```

Run this after sourcing Vivado's environment or using its command prompt. This alternative was not executed during package preparation.

## Rebuild programs and expected results

```sh
python3 tools/build_programs.py
python3 tools/run_regression.py
```

The generator writes the supplied `.S` programs and vectors deterministically. Add your own generated cases in `tools/build_programs.py`; preserve the final `ebreak` for a successful program. Do not manually edit golden trace files to hide a mismatch.

The standard-library assembler supports these instructions, labels, register aliases, `.word` and `nop`. It does not implement the full GNU assembler or arbitrary pseudo-instructions. For a separate source:

```sh
python3 tools/rv32i_asm.py my_program.S my_program.hex
```

Branch/jump labels are preferred. Numeric targets are absolute byte addresses; `.+N` and `.-N` are relative targets.

Optional GNU cross-check (requires RISC-V binutils):

```sh
python3 tools/check_gnu_assembler.py
# For another toolchain:
python3 tools/check_gnu_assembler.py --prefix riscv32-unknown-elf-
```

Optional generic synthesis (requires Yosys):

```sh
python3 tools/run_synthesis.py
```

Optional report regeneration (requires `reportlab` and `matplotlib`):

```sh
python3 tools/generate_report.py
```

## Verified results

| Check actually run | Result |
| --- | --- |
| Five component benches plus processor bench | 6/6 PASS |
| ALU/branch checks | 13,752 |
| Immediate checks | 8,192 |
| Register-file checks | 98 |
| Decoder checks | 2,093 |
| Memory-interface checks | 13 |
| Architectural programs | 52/52 PASS, including 16 fixed random seeds |
| Retirement records checked | 12,604 |
| Final state | 32 registers and 4,096 bytes checked for each program |
| Functional mnemonic bins | 40/40 exercised, including ECALL/EBREAK trap behavior |
| Branch bins | Both outcomes of all six conditions, 12/12 |
| GNU assembler comparison | 52/52 exact machine-code matches |
| Yosys structural synthesis | PASS; no inferred latches |

These are project functional bins, not code coverage, formal proof, exhaustive coverage or official architectural certification. The Python reference model is independent of RTL control encodings but is also project code; a future Spike/Sail or architectural-test integration would strengthen verification.

## Important implementation choices

Loads complete in the same cycle because memory reads are combinational. GPR writeback and PC updates occur on the next rising edge. Clocked-read block RAM cannot replace these memories without redesigning the processor's memory timing.

Faults suppress PC updates, register writes and store strobes. A fault sets sticky `halted` and trap metadata; no instruction retires until synchronous reset. A load to x0 still performs memory checks.

CPU reset clears the PC, registers and trace/trap state. Data memory has no reset port and retains its contents across CPU reset; testbenches explicitly clear memory between programs. See [docs/Interface_Contract.md](docs/Interface_Contract.md).

## Attribution

The learning starting point was [Samad Abbasi's single-cycle project](https://github.com/samad-abbasi/RISC-V-Single-Cycle-Processor), inspected at commit `577eb7e10d091069c6b1e67968ad49eca284749c`. This package is a new implementation, with new names, control definitions, byte-lane memory logic and verification infrastructure. It does not redistribute the reference repository's RTL or report.

Primary ISA reference: [RISC-V RV32I specification](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html).

