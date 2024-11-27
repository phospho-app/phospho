.PHONY: install_deps extractor backend platform all stop

all: install_deps extractor backend platform

install_deps:
	@echo "Installing dependencies for all services"
	pip install poetry
	cd ai_hub && poetry install
	cd extractor && poetry install
	cd backend && poetry install
	cd platform && npm install

temporal:
	@echo "Starting temporal local server"
	temporal server start-dev --db-filename your_temporal.db --ui-port 7999 &

extractor:
	@echo "Starting extractor"
	cd extractor && poetry run python main.py

ai_hub:
	@echo "Starting AI hub"
	cd backend && poetry run python main.py

backend:
	@echo "Starting backend"
	cd backend && poetry run uvicorn app.main:app --reload --port 8000

platform:
	@echo "Starting platform"
	cd platform && npm run dev &
	@echo "🧪🧪🧪 Everything is up and running! Run 'make stop' to stop everything"

stop:
	@echo "Stopping all services"
	-pkill -f 'uvicorn.*7605'
	-pkill -f 'uvicorn.*8000'
	-pkill -f 'node.*platform'