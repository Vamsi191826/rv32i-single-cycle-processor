# 100 MHz design target. No measured Fmax or timing closure is claimed.
create_clock -name core_clk -period 10.000 [get_ports clk]
# External combinational memory paths need board-specific I/O constraints for
# implementation. This package does not provide a board pinout or bitstream.
