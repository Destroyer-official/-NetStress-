# NetStress Makefile
# Production build and development commands

.PHONY: all install install-dev build-native build-native-linux build-native-windows build-native-macos test test-quick test-full lint format clean help setup-linux setup-windows setup-macos

# Default target
all: install

# Detect platform
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM = linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM = macos
endif
ifdef OS
    ifeq ($(OS),Windows_NT)
        PLATFORM = windows
    endif
endif

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev: install
	pip install pytest pytest-cov pytest-asyncio hypothesis maturin black flake8 mypy

# Build native Rust engine (platform-specific)
build-native: build-native-$(PLATFORM)

# Linux-specific build with advanced features
build-native-linux:
	@echo "Building native Rust engine for Linux..."
	cd native/rust_engine && maturin develop --release --features "sendmmsg,io_uring"
	@echo "Linux native engine built successfully!"

# Windows-specific build
build-native-windows:
	@echo "Building native Rust engine for Windows..."
	cd native/rust_engine && maturin develop --release --features "iocp"
	@echo "Windows native engine built successfully!"

# macOS-specific build
build-native-macos:
	@echo "Building native Rust engine for macOS..."
	cd native/rust_engine && maturin develop --release --features "kqueue"
	@echo "macOS native engine built successfully!"

# Build with all available features (Linux only)
build-native-full:
	@echo "Building native Rust engine with all features..."
	cd native/rust_engine && maturin develop --release --features "sendmmsg,io_uring,af_xdp,dpdk"
	@echo "Full-featured native engine built successfully!"

# Build native engine for distribution
build-wheel:
	@echo "Building wheel..."
	cd native/rust_engine && maturin build --release
	@echo "Wheel built in native/rust_engine/target/wheels/"

# Run all tests
test:
	python -m pytest tests/ -v --tb=short

# Run quick smoke tests
test-quick:
	python -m pytest tests/ -v --tb=short -x -q

# Run full test suite with coverage
test-full:
	python -m pytest tests/ -v --tb=short --cov=core --cov-report=term-missing --cov-report=html:coverage_html

# Run specific test file
test-native:
	python -m pytest tests/test_native_engine.py -v --tb=short

test-advanced:
	python -m pytest tests/test_advanced_features.py -v --tb=short

# Lint code
lint:
	flake8 core/ --max-line-length=120 --ignore=E501,W503
	mypy core/ --ignore-missing-imports || true

# Format code
format:
	black core/ tests/ --line-length=120

# Check system status
status:
	python netstress_cli.py --status

# Run with example target (dry run)
demo:
	python netstress_cli.py -t 127.0.0.1 -p 9999 -P UDP -d 5 --dry-run -v

# Clean build artifacts
clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache */.pytest_cache
	rm -rf .coverage coverage_html htmlcov
	rm -rf *.egg-info dist build
	rm -rf native/rust_engine/target
	rm -rf .hypothesis
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# Deep clean including logs and reports
clean-all: clean
	rm -rf *.log logs/ reports/ audit_logs/
	rm -rf crashes/

# Generate documentation
docs:
	@echo "Documentation available in docs/ and README.md"

# Platform-specific setup
setup-linux:
	@echo "Setting up Linux dependencies..."
	sudo apt update || sudo dnf update || true
	sudo apt install -y build-essential libpcap-dev libffi-dev libssl-dev pkg-config || \
	sudo dnf install -y gcc gcc-c++ libpcap-devel libffi-devel openssl-devel pkgconfig || true
	@echo "Linux setup complete!"

setup-windows:
	@echo "Windows setup requires manual installation:"
	@echo "1. Install Visual Studio Build Tools"
	@echo "2. Install Npcap from https://nmap.org/npcap/"
	@echo "3. Run as Administrator for raw socket support"

setup-macos:
	@echo "Setting up macOS dependencies..."
	brew install libpcap openssl pkg-config || true
	xcode-select --install || true
	@echo "macOS setup complete!"

# Show help
help:
	@echo "NetStress Makefile Commands:"
	@echo ""
	@echo "Platform Setup:"
	@echo "  make setup-linux      - Install Linux dependencies"
	@echo "  make setup-windows     - Show Windows setup instructions"
	@echo "  make setup-macos       - Install macOS dependencies"
	@echo ""
	@echo "Installation:"
	@echo "  make install           - Install production dependencies"
	@echo "  make install-dev       - Install development dependencies"
	@echo ""
	@echo "Native Engine Build:"
	@echo "  make build-native      - Build native engine (platform-specific)"
	@echo "  make build-native-linux - Build Linux native engine"
	@echo "  make build-native-windows - Build Windows native engine"
	@echo "  make build-native-macos - Build macOS native engine"
	@echo "  make build-native-full - Build with all features (Linux only)"
	@echo "  make build-wheel       - Build wheel for distribution"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run all tests"
	@echo "  make test-quick        - Run quick smoke tests"
	@echo "  make test-full         - Run full tests with coverage"
	@echo "  make test-native       - Test native engine"
	@echo "  make test-advanced     - Test advanced features"
	@echo ""
	@echo "Development:"
	@echo "  make lint              - Run linters"
	@echo "  make format            - Format code with black"
	@echo "  make status            - Show system status"
	@echo "  make demo              - Run demo (dry run)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make clean-all         - Deep clean including logs"
	@echo ""
	@echo "Platform detected: $(PLATFORM)"
