.PHONY: start stop test lint clean build container-test

# Start the bot
start:
	@echo "Starting Taint-FM Discord Bot..."
	python bot.py

# Stop the bot (sends SIGTERM to processes running bot.py)
stop:
	@echo "Stopping Taint-FM Discord Bot..."
	-pkill -f "python bot.py"

# Run tests using pytest
test:
	@echo "Running tests..."
	pytest --maxfail=1 --disable-warnings -q

# Lint the code using flake8
lint:
	@echo "Linting code..."
	flake8 .

# Clean up __pycache__ directories
clean:
	@echo "Cleaning up..."
	find . -name '__pycache__' -exec rm -rf {} +

# Build the Docker image
build:
	@echo "Building Docker image..."
	docker build -t discord-bot:test .

# Run container structure tests
container-test: build
	@echo "Running container structure tests..."
	container-structure-test test --image discord-bot:test --config tests/container/container-structure-tests.yaml

# Lint the Dockerfile using hadolint
container-lint:
	@echo "Running container hadolint..."
	hadolint Dockerfile
