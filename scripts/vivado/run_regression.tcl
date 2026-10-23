# Batch-only entry point. Runs all testbenches and verifies fresh PASS markers.
source [file join [file dirname [info script]] create_project.tcl]
foreach rv32i_tb {tb_datapath tb_immediate tb_regfile tb_decoder tb_memory tb_system} {
    set rv32i_marker [file join $rv32i_result_dir ${rv32i_tb}.pass]
    file delete -force $rv32i_marker
    set_property top $rv32i_tb [get_filesets sim_1]
    update_compile_order -fileset sim_1
    if {[catch {launch_simulation -mode behavioral; run all; close_sim} rv32i_error]} {
        puts stderr "Simulation failed for $rv32i_tb: $rv32i_error"
        exit 1
    }
    if {![file exists $rv32i_marker]} {puts stderr "PASS marker missing: $rv32i_tb"; exit 1}
    puts "VIVADO_TEST_PASS $rv32i_tb"
}
puts "VIVADO_REGRESSION_PASS"
close_project
exit 0
