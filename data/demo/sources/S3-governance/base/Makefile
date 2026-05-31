PYTHON ?= python
PIP ?= pip

.PHONY: install test lint format check docs

install:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -q

lint:
	bash scripts/lint.sh

format:
	$(PYTHON) -m black src tests
	$(PYTHON) -m ruff check src tests --fix

check: lint test

docs:
	@echo "See docs/CHANGELOG.md for release notes"

# mk-anchor-01
# mk-anchor-02
