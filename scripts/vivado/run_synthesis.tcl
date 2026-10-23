# Core-only synthesis. Clock target is a constraint, not a measured frequency.
source [file join [file dirname [info script]] create_project.tcl]
launch_runs synth_1 -jobs 4
wait_on_run synth_1
set rv32i_status [get_property STATUS [get_runs synth_1]]
if {![string match {*Complete*} $rv32i_status]} {puts stderr "Synthesis did not complete: $rv32i_status"; exit 1}
open_run synth_1
set rv32i_synth_dir [file join $rv32i_root results user_runs vivado_synthesis]
file mkdir $rv32i_synth_dir
report_utilization -hierarchical -file [file join $rv32i_synth_dir utilization.rpt]
report_timing_summary -file [file join $rv32i_synth_dir timing_summary.rpt]
report_methodology -file [file join $rv32i_synth_dir methodology.rpt]
write_checkpoint -force [file join $rv32i_synth_dir rv32i_core_synth.dcp]
puts "VIVADO_SYNTHESIS_COMPLETE. These are synthesis estimates, not routed board results."
close_project
exit 0
