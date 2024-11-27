.PHONY: install temporal ai_hub extractor backend platform all stop

up: temporal ai_hub extractor backend platform all

install:
	@echo "Installing dependencies for all services"
	pip install poetry
	cd ai-hub && poetry install
	cd extractor && poetry install
	cd backend && poetry install
	cd platform && npm install 

temporal:
	@echo "Starting temporal local server"
	temporal server start-dev --db-filename your_temporal.db --ui-port 7999 &

extractor:
	@echo "Starting extractor"
	cd extractor && poetry run python main.py &

ai_hub:
	@echo "Starting AI hub"
	cd ai-hub && poetry run python main.py &

backend:
	@echo "Starting backend"
	cd backend && poetry run uvicorn phospho_backend.main:app --reload --port 8000 &

platform:
	@echo "Starting platform"
	cd platform && npm run dev &
	@echo "\033[1;32m🧪🧪🧪 Everything is up and running! Run 'make stop' to stop everything\033[0m"

stop:
	@echo "Stopping all services"
	@echo "Stopping backend"
	-pkill -f 'uvicorn.*app.phospho_backend:app'
	-pkill -f 'uvicorn.*8000'

	@echo "Stopping ai-hub and extractor"
	-pkill -f 'python.*main.py' 

	@echo "Stopping temporal"
	-pkill -f 'python.*temporal_client'
	-pkill -f 'temporal.*7999'
	-pkill -f 'temporal.*server'
	-pkill -f 'temporal.*client'

	@echo "Stopping platform"
	-pkill -f 'node.*platform'

	@echo "\033[1;32m🛑🛑🛑 Everything stopped\033[0m"
	
