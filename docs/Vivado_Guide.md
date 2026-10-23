# Vivado simulation and synthesis guide

Vivado is not installed in the package preparation environment. The supplied evidence is from Icarus Verilog, GNU binutils and Yosys. The steps below are intended for local Vivado execution; retain your logs.

## GUI: main processor regression

1. Extract the entire ZIP to a writable folder.
2. Open a new Vivado session. The script creates a fresh project under `build/vivado/`.
3. In the Tcl Console, enter:
   ```tcl
   source {C:/RISC_V/RV32I_Single_Cycle_Project/scripts/vivado/create_project.tcl}
   launch_simulation
   run all
   ```
4. Require both `SYSTEM_SUMMARY cases=52 retired=12604` and `TESTBENCH_PASS tb_system`.
5. Check `results/user_runs/xsim/tb_system.pass` and `retire_trace.csv` have new modification times. The batch regression deletes old markers automatically.

The main testbench resets and runs all 52 programs, compares every retire event, checks all final registers and memory bytes, then checks trap/halt stability. A failure issues `$fatal`, rather than merely printing an error.

## Run the six benches

Use a Vivado command prompt in the extracted project root:

```text
vivado -mode batch -source scripts/vivado/run_regression.tcl
```

Require `VIVADO_REGRESSION_PASS`. Individual bench pass messages are also printed. If the simulator fails, the wrapper checks for a fresh PASS marker and returns a nonzero exit code.

To switch benches in the GUI:

```tcl
close_sim
set_property top tb_datapath [get_filesets sim_1]
launch_simulation
run all
```

Available tops: `tb_datapath`, `tb_immediate`, `tb_regfile`, `tb_decoder`, `tb_memory`, `tb_system`.

## Observe the datapath

For the first instruction, launch simulation and run only 100 ns first; use `run all` afterwards. The clock has a 10 ns period. A 10 ns simulation period is a stimulus choice and does not prove a 100 MHz implementation.

In the simulation scope tree, expand `tb_system/dut/u_core`. Add these signals to the Wave window using right-click > Add to Wave Window:

| Group | Signals |
| --- | --- |
| State | `clk`, `rst`, `pc`, `halted` |
| Decode | `instruction`, `alu_operation`, `writeback_select`, `reg_write` |
| Operands | `rs1_data`, `rs2_data`, `immediate`, `alu_a`, `alu_b` |
| Execute/writeback | `alu_result`, `writeback_data`, `register_write_enable` |
| Memory | `dmem_request`, `dmem_address`, `dmem_write_data`, `dmem_write_strobe`, `dmem_read_data` |
| Next PC | `pc_plus4`, `pc_relative_target`, `jalr_target`, `branch_taken`, `next_pc` |
| Checked retirement | `retire_valid`, `trace_pc`, `trace_instruction`, `trace_rd_write`, `trace_rd_data` |
| Faults | `pending_trap`, `trap_cause`, `trap_pc`, `trap_value` |

Use hexadecimal radix for addresses, instructions and data. Use unsigned radix for register indices and control fields. For `retire_valid=1`, the registered trace describes the instruction that just completed, while the live PC/instruction normally describes the next instruction. That one-instruction observation offset is expected.

The provided `results/verified/iverilog/system.vcd` is an actual portable-simulator waveform, not a Vivado capture.

## Core synthesis

From the project root:

```text
vivado -mode batch -source scripts/vivado/run_synthesis.tcl
```

Outputs under `results/user_runs/vivado_synthesis/`:

- `utilization.rpt`: hierarchical core utilization.
- `timing_summary.rpt`: synthesis timing estimates.
- `methodology.rpt`: implementation concerns.
- `rv32i_core_synth.dcp`: synthesized checkpoint.

The script synthesizes `rv32i_core` with external memory ports, not a constant demonstration ROM that could optimize away meaningful logic. Debug and trace circuitry are retained and affect area.

The clock constraint is 10 ns. No board pin constraints, external I/O timing constraints, placement, routing or bitstream flow is provided. A core-only synthesis timing report is not enough to claim board timing closure or Fmax.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Device part not installed | Set `RV32I_PART` to an installed part before project creation, or install the Zynq-7000 device support |
| `Cannot open ...hex` | Extract all folders; inspect ROOT plusarg and project path |
| `Cannot create PASS marker` | Results folder must be writable; script creates it |
| Include/header not found | Use the project-creation script instead of adding only the top RTL |
| Old program still appears | Regenerate vectors, relaunch simulation; do not reuse old pass markers |
| Simulation opens but stays at time 0 | Run `run all`; the project intentionally starts at 0 ns |
| Assertion/trace mismatch | Save the case name, step, expected and actual words before changing RTL |
| Compile/property error in another Vivado release | Keep the log; verify supported XSim properties in that release's official documentation |

Sources: AMD UG900 (Vivado Logic Simulation) and UG835 (`launch_simulation`). See report references.

