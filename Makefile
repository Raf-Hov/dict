PYTHON = python3
MAIN = src

run:
	$(PYTHON) -m $(MAIN)

web:
	$(PYTHON) -m $(MAIN) --web

cli:
	$(PYTHON) -m $(MAIN) --cli

manage:
	$(PYTHON) -m $(MAIN) --manage