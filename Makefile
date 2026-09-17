.PHONY: test assemble-examples run-test run-multiplication run-multiplication-bin run-square gui-multiplication clean

PYTHON ?= python

test:
	$(PYTHON) -m unittest discover -s tests -v

assemble-examples:
	@for file in programs/*.asm; do \
		echo "Assembling $$file"; \
		$(PYTHON) assemblerasm.py "$$file"; \
	done

run-test:
	$(PYTHON) cpu.py programs/test.mc --max-steps 1000

run-multiplication:
	$(PYTHON) cpu.py programs/multiplication.mc --max-steps 1000

run-multiplication-bin:
	$(PYTHON) cpu.py programs/multiplication.bin --max-steps 1000

run-square:
	$(PYTHON) cpu.py programs/square.mc --max-steps 1000

gui-multiplication:
	$(PYTHON) compute.py programs/multiplication.mc --clock 2

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
