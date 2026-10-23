# Run in a NEW Vivado GUI session: source C:/RV32I_Single_Cycle_Project/scripts/vivado/create_project.tcl
# Batch: vivado -mode batch -source scripts/vivado/create_project.tcl
set rv32i_root [file normalize [file join [file dirname [info script]] ../..]]
set rv32i_part xc7z020clg400-1
if {[info exists ::env(RV32I_PART)]} {set rv32i_part $::env(RV32I_PART)}
set rv32i_project_dir [file join $rv32i_root build vivado]
set rv32i_result_dir [file join $rv32i_root results user_runs xsim]
file mkdir $rv32i_result_dir
create_project -force rv32i_single_cycle $rv32i_project_dir -part $rv32i_part
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property target_simulator XSim [current_project]
add_files -norecurse [glob [file join $rv32i_root rtl *.v]]
add_files -norecurse [file join $rv32i_root rtl rv32i_defs.vh]
set_property include_dirs [list [file join $rv32i_root rtl]] [get_filesets sources_1]
set_property top rv32i_core [get_filesets sources_1]
add_files -fileset constrs_1 -norecurse [file join $rv32i_root constraints core_clock.xdc]
add_files -fileset sim_1 -norecurse [glob [file join $rv32i_root tb *.sv]]
add_files -fileset sim_1 -norecurse [file join $rv32i_root tb tb_common.svh]
add_files -fileset sim_1 -norecurse [file join $rv32i_root tb generated case_list.svh]
set_property file_type {Verilog Header} [get_files -all *.svh]
set_property include_dirs [list [file join $rv32i_root rtl] [file join $rv32i_root tb] [file join $rv32i_root tb generated]] [get_filesets sim_1]
set_property top tb_system [get_filesets sim_1]
set_property xsim.simulate.runtime 0ns [get_filesets sim_1]
set_property xsim.simulate.xsim.more_options [format {-testplusarg "ROOT=%s" -testplusarg "OUT=%s"} $rv32i_root $rv32i_result_dir] [get_filesets sim_1]
set_property xsim.simulate.log_all_signals true [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
puts "RV32I project created. Simulation top=tb_system; synthesis top=rv32i_core."
puts "Simulation: launch_simulation; run all"
puts "Expected full regression: 52 CASE_PASS lines and TESTBENCH_PASS tb_system."
