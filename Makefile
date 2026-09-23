PYTHON ?= python3
VENV := $(CURDIR)/.venv
PY := $(VENV)/bin/python

.PHONY: setup seed dev test eval build
setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -e './backend[dev]'
	cd frontend && npm install

seed:
	$(PY) -m app.seed

dev: seed
	$(PY) scripts/dev.py

test:
	$(PY) -m pytest backend/tests -q
	cd frontend && npm run typecheck

eval:
	$(PY) -m app.evaluate

build:
	cd frontend && npm run build
