.PHONY: install_deps extractor backend platform all stop

all: install_deps extractor backend platform

install_deps:
	@echo "Installing dependencies for all services..."
	cd extractor && poetry install --with dev
	cd backend && poetry install --with dev
	cd platform && npm install

extractor:
	@echo "Starting extractor..."
	cd extractor && poetry run uvicorn app.main:app --reload --port 7605 &

backend:
	@echo "Starting backend..."
	cd backend && poetry run uvicorn app.main:app --reload --port 8000 &

platform:
	@echo "Starting platform..."
	cd platform && npm run dev &
	@echo "🧪🧪🧪 Everything is up and running! Run 'make stop' to stop everything"

stop:
	@echo "Stopping all services..."
	-pkill -f 'uvicorn.*7605'
	-pkill -f 'uvicorn.*8000'
	-pkill -f 'node.*platform'