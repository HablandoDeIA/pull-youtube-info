UV ?= uv
PYTHON := .venv/bin/python
RUN_ARGS :=
ifneq ($(strip $(CHANNEL)),)
RUN_ARGS += --channel "$(CHANNEL)"
endif

.PHONY: help venv install run clean

help: ## Show available targets
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "; OFS=" - "} {printf "  %-10s %s\n", $$1, $$2}'

venv: ## Create the uv-managed virtual environment if missing
	@if [ ! -d ".venv" ]; then \
		$(UV) venv; \
	else \
		echo ".venv already exists; skipping uv venv"; \
	fi

install: venv ## Install dependencies into the virtual environment
	$(UV) pip install -r requirements.txt

run: install ## Execute the script using uv (loads .env automatically)
	$(UV) run $(PYTHON) youtube_info.py $(RUN_ARGS)

clean: ## Remove the virtual environment
	rm -rf .venv
