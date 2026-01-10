.PHONY: install run shell clean help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install  Install dependencies with pipenv"
	@echo "  run      Run the snake game"
	@echo "  shell    Activate the pipenv shell"
	@echo "  clean    Remove virtual environment"
	@echo "  help     Show this help message"

install:
	pipenv install

run:
	pipenv run python main.py

shell:
	pipenv shell

clean:
	pipenv --rm
