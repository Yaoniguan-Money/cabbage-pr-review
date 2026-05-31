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

coverage:
	$(PYTHON) -m pytest tests/ --cov=src/app --cov-report=term-missing

audit-deps:
	$(PIP) list --outdated

ci: lint test coverage

release-check: ci audit-deps
	@echo "Release gate passed"

docker-build:
	docker build -t governance-demo:local .

docker-run:
	docker run --rm -p 8080:8080 governance-demo:local

seed-demo:
	$(PYTHON) -c "from app.service import GovernanceService; print(GovernanceService().export_snapshot())"

typecheck:
	$(PYTHON) -m mypy src/app

security-scan:
	$(PYTHON) -m bandit -r src/app -q

clean:
	rm -rf .pytest_cache .mypy_cache htmlcov dist build
