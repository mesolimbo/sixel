.PHONY: install install-dev run shell clean dist unit e2e e2e-docker docker-build coverage help

DIST_NAME = sixel-snake
DIST_DIR = dist
DOCKER_IMAGE = sixel-snake-test

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install dependencies with pipenv"
	@echo "  install-dev   Install with dev dependencies (pytest)"
	@echo "  run           Run the snake game"
	@echo "  shell         Activate the pipenv shell"
	@echo "  clean         Remove virtual environment and build artifacts"
	@echo "  dist          Create zip for itch.io distribution"
	@echo "  unit          Run unit tests"
	@echo "  e2e           Run E2E render tests locally with pytest"
	@echo "  e2e-docker    Run E2E tests in Docker (builds image first)"
	@echo "  docker-build  Build the Docker test image locally"
	@echo "  coverage      Run tests with coverage report"
	@echo "  help          Show this help message"

install:
	pipenv install

install-dev:
	pipenv install --dev

run:
	pipenv run python main.py

shell:
	pipenv shell

clean:
	pipenv --rm

dist:
	@echo "Creating distribution zip..."
	rm -rf $(DIST_DIR)
	mkdir -p $(DIST_DIR)/$(DIST_NAME)
	cp -r main.py game.py game_loop.py renderer.py sixel.py terminals/ demo/ $(DIST_DIR)/$(DIST_NAME)/
	cp Pipfile Makefile README.md $(DIST_DIR)/$(DIST_NAME)/
	cd $(DIST_DIR) && zip -r $(DIST_NAME).zip $(DIST_NAME)
	rm -rf $(DIST_DIR)/$(DIST_NAME)
	@echo "Created $(DIST_DIR)/$(DIST_NAME).zip"

# Testing targets
unit:
	pipenv run python -m pytest tests/ -v --ignore=tests/test_render_e2e.py --ignore=tests/test_screenshot.py

e2e:
	pipenv run pytest tests/test_render_e2e.py tests/test_screenshot.py -v --tb=short

e2e-docker: docker-build
	docker run --rm $(DOCKER_IMAGE)

coverage:
	pipenv run python -m pytest tests/ --cov=. --cov-report=term-missing

# Docker targets
docker-build:
	docker build -t $(DOCKER_IMAGE) .
