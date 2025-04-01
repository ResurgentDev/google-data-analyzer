# Default target
.DEFAULT_GOAL := help

# Install base dependencies
install:
    pip install -r requirements.txt

# Install dev dependencies
install-dev:
    pip install -r requirements-dev.txt

# Run tests
test:
    pytest tests/

# Format code
format:
    black src/

# Lint code
lint:
    flake8 src/

# Display help
help:
    @echo "Available commands:"
    @echo "  make install     Install dependencies"
    @echo "  make test        Run tests"
    @echo "  make format      Format code"
    @echo "  make lint        Lint code"
