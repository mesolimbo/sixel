.PHONY: install install-dev run shell clean dist unit e2e test coverage help

DIST_NAME = gui
DIST_DIR = dist

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install dependencies with pipenv"
	@echo "  install-dev   Install with dev dependencies (pytest)"
	@echo "  run           Run GUI demo"
	@echo "  shell         Activate the pipenv shell"
	@echo "  clean         Remove virtual environment and build artifacts"
	@echo "  dist          Create zip for distribution"
	@echo "  unit          Run unit tests (excludes e2e)"
	@echo "  e2e           Run end-to-end tests"
	@echo "  test          Run all tests (unit + e2e)"
	@echo "  coverage      Run tests with coverage report"
	@echo "  help          Show this help message"

install:
	pipenv install

install-dev:
	pipenv install --dev

run:
	pipenv run python main.py demo.yaml

shell:
	pipenv shell

clean:
	pipenv --rm

dist:
	@echo "Creating distribution zip..."
	rm -rf $(DIST_DIR)
	mkdir -p $(DIST_DIR)/$(DIST_NAME)
	cp -r main.py app_loop.py renderer.py sixel.py gui.py terminals/ $(DIST_DIR)/$(DIST_NAME)/
	cp Pipfile Makefile README.md $(DIST_DIR)/$(DIST_NAME)/
	cd $(DIST_DIR) && zip -r $(DIST_NAME).zip $(DIST_NAME)
	rm -rf $(DIST_DIR)/$(DIST_NAME)
	@echo "Created $(DIST_DIR)/$(DIST_NAME).zip"

# Testing targets
unit:
	pipenv run python -m pytest tests/ -v --ignore=tests/test_render_e2e.py --ignore=tests/test_screenshot.py

e2e:
	pipenv run python -m pytest tests/test_render_e2e.py tests/test_screenshot.py -v

test:
	pipenv run python -m pytest tests/ -v

coverage:
	pipenv run python -m pytest tests/ --cov=. --cov-report=term-missing
