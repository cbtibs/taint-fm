# Makefile for Taint-FM Discord Bot

.PHONY: start stop test lint clean

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
