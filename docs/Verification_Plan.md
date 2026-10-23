# Verification plan and evidence

The oracle is `tools/reference_model.py`, an architectural interpreter that uses Python integers and a bytearray. It does not import RTL control encodings. Its store operation writes individual bytes; the RTL uses an aligned-word bus with strobes.

Program words were independently compared with GNU RISC-V assembler/linker output. This checks the assembler, not the entire architectural oracle.

## Testbenches

| Testbench | Checked behavior | Actual checks |
| --- | --- | ---: |
| tb_datapath | All 10 ALU operations; zero flag; signed/unsigned branch conditions; shifts and integer corners | 13,752 |
| tb_immediate | I/S/B/U/J formats, sign extension, low-bit alignment, default formats | 8,192 |
| tb_regfile | Two reads, debug reads, before/after edge writes, x0, write-disable, synchronous reset | 98 |
| tb_decoder | Legal controls and exhaustive funct7 space for R/OP-IMM, illegal widths/opcodes | 2,093 |
| tb_memory | Asynchronous reads, bounds, edge-timed writes, byte and halfword neighbor preservation | 13 |
| tb_system | Architectural trace, final state, traps, halt stability, reset, side-effect suppression | 52 programs |

The check counts are assertion evaluations, not unique architectural instruction counts.

## Program categories

- `directed_isa`: all normal instruction families, arithmetic boundaries, dependencies, byte lanes, signed loads, jumps, x0 and all branch outcomes.
- `fibonacci`: 12 generated numbers stored at addresses 128..175.
- `bubble_sort`: signed ascending sort of nine integers including duplicates, negative numbers and INT_MIN/INT_MAX.
- `random_00`..`random_15`: deterministic seeds 0x51C000..0x51C00F; 400 generation blocks per program, including bounded loops and jump sequences.
- 33 environment/fault/boundary programs: illegal funct7 and shifts, unsupported CSR/FENCE.I, width encoding errors, ECALL, misaligned jumps/loads/stores, out-of-range addresses, load-to-x0 fault, taken/untaken misaligned branch target.

The main bench compares every retirement event with a committed golden record using case equality (`!==` detects X/Z). It checks all 32 final GPRs and all 4096 bytes of memory per case, trap cause/PC/value, no side effects on a fault, and three additional halted cycles.

A watchdog limits instruction count. The Python launcher additionally limits a simulator process to 600 wall-clock seconds.

## Functional coverage

The suite exercises 40 mnemonic groups: 37 datapath instructions, FENCE, ECALL and EBREAK. ECALL/EBREAK are observed as traps, not retirements. Both outcomes of every branch are exercised (12 bins). These are software counters over trace-checked programs, not simulator line/toggle coverage.

Actual totals: 52 programs, 16 random seeds, 12,604 successful retirement events.

## Evidence layout

- `results/verified/iverilog/`: component/system logs, compile logs, six fresh PASS markers, retire CSV, actual VCD and JSON summary with source hashes.
- `results/verified/gnu/gnu_assembler_check.json`: 52 image matches.
- `results/verified/yosys/`: synthesis log, statistics, netlist and structural summary.

Compiled simulator binaries and temporary GNU object/ELF files are omitted from the deliverable; source and commands reproduce them.

## Limits and next verification work

This is a bounded project regression. It does not prove all programs, all memory sizes, timing closure or architectural certification. The oracle is custom software rather than Spike/Sail. Future work can add RISC-V architectural tests, independent Spike/Sail comparison, formal properties and measured simulator code coverage.

Vivado scripts are included for reproduction. XSim and Vivado synthesis were not executed during preparation; no Vivado or board metrics are supplied.

