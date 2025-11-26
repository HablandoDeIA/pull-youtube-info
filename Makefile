UV ?= uv
PYTHON := .venv/bin/python

.PHONY: venv install run clean

venv:
	$(UV) venv

install: venv
	$(UV) pip install -r requirements.txt

run: install
	$(UV) run $(PYTHON) youtube_info.py

clean:
	rm -rf .venv
