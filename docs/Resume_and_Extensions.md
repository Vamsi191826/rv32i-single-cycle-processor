# Resume and extension notes

Use claims that you understand and can demonstrate. Read the RTL and reproduce the tests before presenting this as your own engineering work. This package was generated as a learning starting point.

## Suggested bullets after you review and reproduce the project

- Implemented a modular 32-bit single-cycle RISC-V core covering 37 RV32I datapath instructions, branch/jump control, subword memory operations, and fault reporting.
- Built six self-checking SystemVerilog testbenches and a Python architectural reference flow; checked 52 programs and 12,604 instruction events, including 16 deterministic random seeds.
- Verified byte strobes, signed loads, x0 protection, JALR target masking and fault-side-effect suppression; independently checked program encodings with GNU binutils.

Add Vivado, device utilization or frequency claims only after your own runs. Keep the Vivado logs and clearly identify synthesis estimates versus post-route results. Do not describe this as UVM, formal verification, an operating-system-capable processor or a hardware-demonstrated design.

## A staged extension path

| Stage | Concrete work | Evidence to collect |
| --- | --- | --- |
| 1: Reproduce | Run all Vivado benches; explain ADD/LW/JAL flow | Fresh logs and your waveform screenshots |
| 2: Verify further | Integrate an independent simulator or architectural tests | Test list, signatures, mismatch investigation |
| 3: FPGA memory | Add a multi-cycle memory handshake and synchronous BRAM | Tests with variable latency; synthesis reports |
| 4: Pipeline | Five stages, forwarding, stalls, branch flush | Hazard matrix and unchanged architectural results |
| 5: System | UART, timer, interrupt/CSR support as a separate design | Firmware demonstration and documented trap handling |

Do one stage at a time. For a pipeline, preserve the architectural trace checker so the same programs still produce the same visible results.

