# Makefile for PCD Visualizer - Cross-platform build automation
# Supports Windows, macOS, and Linux development workflows

PYTHON := python3
PIP := pip3
PACKAGE_NAME := pcd-visualizer
VERSION := 2.0.0

# Detect operating system
UNAME := $(shell uname -s)
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    PYTHON := python
    PIP := pip
else ifeq ($(UNAME),Darwin)
    DETECTED_OS := macOS
else ifeq ($(UNAME),Linux)
    DETECTED_OS := Linux
else
    DETECTED_OS := Unknown
endif

# Default target
.PHONY: help
help: ## Show this help message
	@echo "PCD Visualizer Build System ($(DETECTED_OS))"
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment setup
.PHONY: install
install: ## Install runtime dependencies
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

.PHONY: install-build
install-build: ## Install build dependencies
	$(PIP) install -r requirements-build.txt

.PHONY: install-all
install-all: install install-dev install-build ## Install all dependencies

# Development
.PHONY: run
run: ## Run the application in development mode
	$(PYTHON) -m pcd_visualizer.main

.PHONY: test
test: ## Run tests
	pytest tests/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	pytest tests/ -v --cov=pcd_visualizer --cov-report=html

.PHONY: lint
lint: ## Run code linting
	flake8 pcd_visualizer/
	mypy pcd_visualizer/

.PHONY: format
format: ## Format code with black
	black pcd_visualizer/

.PHONY: format-check
format-check: ## Check code formatting
	black --check pcd_visualizer/

# Cleaning
.PHONY: clean
clean: ## Clean build artifacts
	$(PYTHON) build.py --clean
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: clean-all
clean-all: clean ## Clean everything including virtual environments
	rm -rf venv/ .venv/ env/
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/

# Building - Cross Platform
.PHONY: build
build: install-build ## Build package for current platform
	$(PYTHON) build.py

.PHONY: build-all
build-all: install-build ## Build all targets for current platform
	$(PYTHON) build.py --target all

# Windows specific
.PHONY: build-exe
build-exe: install-build ## Build Windows executable
ifeq ($(DETECTED_OS),Windows)
	$(PYTHON) build.py --target exe
else
	@echo "❌ Windows executable can only be built on Windows"
	@exit 1
endif

.PHONY: build-msi
build-msi: install-build ## Build Windows MSI installer
ifeq ($(DETECTED_OS),Windows)
	$(PYTHON) build.py --target msi
else
	@echo "❌ Windows MSI can only be built on Windows"
	@exit 1
endif

# macOS specific
.PHONY: build-app
build-app: install-build ## Build macOS application bundle
ifeq ($(DETECTED_OS),macOS)
	$(PYTHON) build.py --target app
else
	@echo "❌ macOS app bundle can only be built on macOS"
	@exit 1
endif

.PHONY: build-dmg
build-dmg: install-build ## Build macOS DMG installer
ifeq ($(DETECTED_OS),macOS)
	$(PYTHON) build.py --target dmg
else
	@echo "❌ macOS DMG can only be built on macOS"
	@exit 1
endif

# Package management
.PHONY: sdist
sdist: ## Create source distribution
	$(PYTHON) setup.py sdist

.PHONY: wheel
wheel: ## Create wheel distribution
	$(PYTHON) setup.py bdist_wheel

.PHONY: upload-test
upload-test: sdist wheel ## Upload to test PyPI
	$(PIP) install twine
	twine upload --repository testpypi dist/*

.PHONY: upload
upload: sdist wheel ## Upload to PyPI
	$(PIP) install twine
	twine upload dist/*

# Development environment
.PHONY: venv
venv: ## Create virtual environment
	$(PYTHON) -m venv venv
ifeq ($(DETECTED_OS),Windows)
	@echo "Activate with: venv\\Scripts\\activate"
else
	@echo "Activate with: source venv/bin/activate"
endif

.PHONY: docker-build
docker-build: ## Build Docker image for testing
	docker build -t $(PACKAGE_NAME):$(VERSION) .

.PHONY: docker-run
docker-run: docker-build ## Run in Docker container
	docker run -it --rm -e DISPLAY=$$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix $(PACKAGE_NAME):$(VERSION)

# Documentation
.PHONY: docs
docs: ## Generate documentation
	$(PIP) install sphinx sphinx-rtd-theme
	cd docs && sphinx-build -b html . _build/html

.PHONY: docs-serve
docs-serve: docs ## Serve documentation locally
	cd docs/_build/html && $(PYTHON) -m http.server 8000

# Release management
.PHONY: version
version: ## Show current version
	@echo "Current version: $(VERSION)"
	@echo "Detected OS: $(DETECTED_OS)"
	@echo "Python: $(shell $(PYTHON) --version)"

.PHONY: check
check: format-check lint test ## Run all checks (format, lint, test)

.PHONY: ci
ci: install-all check build ## Run CI pipeline (install, check, build)

# Quick development workflow
.PHONY: dev
dev: install-dev format lint run ## Quick dev workflow (install, format, lint, run)

# Platform-specific quick builds
ifeq ($(DETECTED_OS),Windows)
.PHONY: quick-build
quick-build: build-msi ## Quick build for Windows (MSI)
else ifeq ($(DETECTED_OS),macOS)
.PHONY: quick-build
quick-build: build-dmg ## Quick build for macOS (DMG)
else
.PHONY: quick-build
quick-build: build ## Quick build for current platform
endif