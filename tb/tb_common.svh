// Included inside each testbench module. No UVM or vendor libraries required.
string project_root;
string output_directory;
reg [31:0] random_state = 32'h5a17cafe;
function automatic [31:0] random_word;
    begin
        random_state = random_state * 32'd1664525 + 32'd1013904223;
        random_word = random_state;
    end
endfunction
task automatic configure_paths;
    begin
        if (!$value$plusargs("ROOT=%s", project_root)) project_root = ".";
        if (!$value$plusargs("OUT=%s", output_directory)) output_directory = {project_root, "/results/user_runs"};
    end
endtask
task automatic require_file(input string path);
    integer handle;
    begin
        handle = $fopen(path, "r");
        if (handle == 0) $fatal(1, "Cannot open %s. Check ROOT plusarg and extracted folder.", path);
        $fclose(handle);
    end
endtask
task automatic mark_pass(input string test_name);
    integer handle;
    begin
        handle = $fopen({output_directory, "/", test_name, ".pass"}, "w");
        if (handle == 0) $fatal(1, "Cannot create PASS marker in %s", output_directory);
        $fdisplay(handle, "TESTBENCH_PASS %s", test_name);
        $fclose(handle);
        $display("TESTBENCH_PASS %s", test_name);
    end
endtask
