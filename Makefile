UV := uv

.PHONY: help install browsers test test-live lint format typecheck check-records verify clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## create .venv with bookworm (editable) and the dev tools
	$(UV) sync

browsers: ## download the Chromium build Playwright pins (only browser adapters need it)
	$(UV) run playwright install chromium

test: ## the offline suite; ID=DIR-002 (or "DIR-002 CAT-001") runs only those cases
	$(UV) run pytest -v $(foreach id,$(ID),--test-id $(id))

test-live: ## only the tests that talk to real catalogues (network, slow, polite)
	$(UV) run pytest -v -m live $(foreach id,$(ID),--test-id $(id))

lint: ## ruff + import-linter (the layering rules in CLAUDE.md)
	$(UV) run ruff check src tests
	$(UV) run ruff format --check src tests
	$(UV) run lint-imports

format: ## apply ruff's formatting and safe fixes
	$(UV) run ruff format src tests
	$(UV) run ruff check --fix src tests

typecheck: ## mypy --strict on src
	$(UV) run mypy

check-records: ## validate every file in data/ against the record models
	$(UV) run bookworm records check

verify: lint typecheck test check-records ## everything CI runs

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache .import_linter_cache
