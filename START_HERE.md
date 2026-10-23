# Start here

This package contains a new 32-bit single-cycle RISC-V implementation, not a patched copy of the reference repository.

**First goal:** run the processor testbench in Vivado and see `TESTBENCH_PASS tb_system`.

## 1. Extract the whole ZIP

Use a short folder such as `C:/RISC_V/RV32I_Single_Cycle_Project`. Keep the folders together. Do not open the ZIP directly in Vivado.

## 2. Create the Vivado project

Open a new Vivado GUI session. In the Tcl Console, run the following command, replacing the path with your extracted folder:

```tcl
source {C:/RISC_V/RV32I_Single_Cycle_Project/scripts/vivado/create_project.tcl}
```

The script adds every RTL file, testbench, include directory and clock constraint. The default FPGA part is `xc7z020clg400-1`. For simulation, you only need that device family installed. To use another installed part, set the following before sourcing the script:

```tcl
set ::env(RV32I_PART) YOUR_INSTALLED_PART_NAME
```

## 3. Run the main processor simulation

```tcl
launch_simulation
run all
```

Wait for these messages:

```text
SYSTEM_SUMMARY cases=52 retired=12604
TESTBENCH_PASS tb_system
```

A failure stops with `$fatal`. A waveform by itself is not a pass.

## 4. Run all six testbenches

Open a Vivado command prompt, change to the extracted project folder, then run:

```text
vivado -mode batch -source scripts/vivado/run_regression.tcl
```

On Windows, `verify_vivado.bat` runs the same command after Vivado has been added to PATH. The final message must be `VIVADO_REGRESSION_PASS`.

**No Python installation is needed for these Vivado runs.** The generated programs and expected results are already included.

## 5. Start reading

Read `docs/Design_and_Verification_Report.pdf`, then study these files in order:

1. `rtl/rv32i_pc.v` and `rtl/rv32i_memory.v`: instruction fetch.
2. `rtl/rv32i_regfile.v`: two reads and one clocked write.
3. `rtl/rv32i_immediate.v`, `rtl/rv32i_alu.v`: operands and computation.
4. `rtl/rv32i_decoder.v`: instruction-to-control mapping.
5. `rtl/rv32i_core.v`: writeback, next PC and fault handling.
6. `tb/tb_system.sv`: automatic architectural checks.

The report explains the flow with ADD, LW, SW, branches and JAL/JALR before discussing verification.

## What has already been verified?

Icarus Verilog 12.0 passed all six testbenches, 52 programs and 12,604 retirement events. Final registers, all 4 KiB of data memory and trap metadata were checked for every program. GNU assembler matched all 52 machine-code images; Yosys generic core synthesis passed with no inferred latches.

**Vivado/XSim, Vivado synthesis and FPGA hardware runs have not been executed in this package's preparation environment.** Run the included scripts locally and keep your new results in `results/user_runs/`.

