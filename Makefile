.PHONY: test programs waves synth
test:
	python3 tools/run_regression.py
programs:
	python3 tools/build_programs.py
waves:
	python3 tools/run_regression.py --waves
synth:
	python3 tools/run_synthesis.py
