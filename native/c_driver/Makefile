# Makefile for C Driver Unit Tests

CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g
LDFLAGS = 
INCLUDES = -I.

# Platform-specific settings
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    CFLAGS += -D__linux__
    LDFLAGS += -lpthread
endif

ifeq ($(UNAME_S),Darwin)
    CFLAGS += -D__APPLE__
endif

# Windows (MinGW)
ifeq ($(OS),Windows_NT)
    CFLAGS += -D_WIN32
    LDFLAGS += -lws2_32
    EXE_EXT = .exe
else
    EXE_EXT =
endif

# Source files
DRIVER_SRC = driver_shim.c
TEST_SRC = test_driver.c
TEST_TARGET = test_driver$(EXE_EXT)

# Optional feature flags (uncomment to enable)
# CFLAGS += -DHAS_DPDK
# CFLAGS += -DHAS_AF_XDP
# CFLAGS += -DHAS_IO_URING

# Default target
all: $(TEST_TARGET)

# Build test executable
$(TEST_TARGET): $(TEST_SRC) $(DRIVER_SRC) test_framework.h driver_shim.h
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $(TEST_SRC) $(DRIVER_SRC) $(LDFLAGS)

# Run tests
test: $(TEST_TARGET)
	./$(TEST_TARGET)

# Run tests with verbose output
test-verbose: $(TEST_TARGET)
	./$(TEST_TARGET) -v

# Clean build artifacts
clean:
	rm -f $(TEST_TARGET)
	rm -f *.o
	rm -f core
	rm -f vgcore.*

# Memory check with valgrind (Linux only)
memcheck: $(TEST_TARGET)
ifeq ($(UNAME_S),Linux)
	valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./$(TEST_TARGET)
else
	@echo "Valgrind not available on this platform"
endif

# Static analysis with cppcheck
analyze:
	cppcheck --enable=all --std=c99 --platform=unix64 $(DRIVER_SRC) $(TEST_SRC)

# Code coverage (requires gcov)
coverage: CFLAGS += -fprofile-arcs -ftest-coverage
coverage: LDFLAGS += -lgcov
coverage: clean $(TEST_TARGET)
	./$(TEST_TARGET)
	gcov $(DRIVER_SRC)
	@echo "Coverage report generated in *.gcov files"

# Debug build
debug: CFLAGS += -DDEBUG -O0
debug: $(TEST_TARGET)

# Release build
release: CFLAGS += -DNDEBUG -O3
release: $(TEST_TARGET)

# Install (copy to system location)
install: $(TEST_TARGET)
	@echo "Installing test binary to /usr/local/bin (requires sudo)"
	sudo cp $(TEST_TARGET) /usr/local/bin/

# Uninstall
uninstall:
	sudo rm -f /usr/local/bin/$(TEST_TARGET)

# Help
help:
	@echo "Available targets:"
	@echo "  all        - Build test executable (default)"
	@echo "  test       - Build and run tests"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  clean      - Remove build artifacts"
	@echo "  memcheck   - Run tests with valgrind (Linux only)"
	@echo "  analyze    - Run static analysis with cppcheck"
	@echo "  coverage   - Build with coverage and generate report"
	@echo "  debug      - Build debug version"
	@echo "  release    - Build optimized release version"
	@echo "  install    - Install test binary system-wide"
	@echo "  uninstall  - Remove installed binary"
	@echo "  help       - Show this help message"

# Phony targets
.PHONY: all test test-verbose clean memcheck analyze coverage debug release install uninstall help