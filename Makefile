PYTHON ?= python3
HOST ?= 0.0.0.0
PORT ?= 8080

run:
	$(PYTHON) main.py

web:
	$(PYTHON) main.py --web --host $(HOST) --port $(PORT)

cli:
	$(PYTHON) main.py --cli

manage:
	$(PYTHON) main.py --manage

ish-setup:
	@echo "Installing python3 on iSH (Alpine Linux)..."
	apk update && apk add python3