.PHONY: install run shell clean dist help

DIST_NAME = sixel-snake
DIST_DIR = dist

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install  Install dependencies with pipenv"
	@echo "  run      Run the snake game"
	@echo "  shell    Activate the pipenv shell"
	@echo "  clean    Remove virtual environment"
	@echo "  dist     Create zip for itch.io distribution"
	@echo "  help     Show this help message"

install:
	pipenv install

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
	cp -r main.py game.py game_loop.py renderer.py sixel.py terminals/ $(DIST_DIR)/$(DIST_NAME)/
	cp Pipfile README.md $(DIST_DIR)/$(DIST_NAME)/
	cd $(DIST_DIR) && zip -r $(DIST_NAME).zip $(DIST_NAME)
	rm -rf $(DIST_DIR)/$(DIST_NAME)
	@echo "Created $(DIST_DIR)/$(DIST_NAME).zip"
