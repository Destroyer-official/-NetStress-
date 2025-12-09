#!/bin/bash
# Advanced DDoS Testing Framework - Installation Script for Linux/macOS
# This script automates the installation process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRAMEWORK_NAME="Advanced DDoS Testing Framework"
REPO_URL="https://github.com/ddos-framework/advanced-ddos-framework.git"
INSTALL_DIR="$HOME/.ddos-framework"
PYTHON_MIN_VERSION="3.8"

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  $FRAMEWORK_NAME${NC}"
    echo -e "${BLUE}  Installation Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

check_os() {
    print_step "Detecting operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_info "Detected: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_info "Detected: macOS"
    else
        print_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

check_python() {
    print_step "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python $PYTHON_MIN_VERSION or higher."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    
    if $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_info "Python $PYTHON_VERSION found (OK)"
    else
        print_error "Python $PYTHON_VERSION found, but $PYTHON_MIN_VERSION or higher is required."
        exit 1
    fi
}

check_pip() {
    print_step "Checking pip installation..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        print_error "pip not found. Please install pip."
        exit 1
    fi
    
    print_info "pip found: $PIP_CMD"
}

install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    if [[ "$OS" == "linux" ]]; then
        # Detect Linux distribution
        if command -v apt-get &> /dev/null; then
            print_info "Detected Debian/Ubuntu system"
            sudo apt-get update
            sudo apt-get install -y \
                build-essential \
                libpcap-dev \
                libffi-dev \
                libssl-dev \
                pkg-config \
                git \
                curl
        elif command -v yum &> /dev/null; then
            print_info "Detected RHEL/CentOS system"
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y \
                libpcap-devel \
                libffi-devel \
                openssl-devel \
                pkgconfig \
                git \
                curl
        elif command -v dnf &> /dev/null; then
            print_info "Detected Fedora system"
            sudo dnf groupinstall -y "Development Tools"
            sudo dnf install -y \
                libpcap-devel \
                libffi-devel \
                openssl-devel \
                pkgconfig \
                git \
                curl
        else
            print_warning "Unknown Linux distribution. Please install dependencies manually:"
            print_info "- build-essential/Development Tools"
            print_info "- libpcap-dev/libpcap-devel"
            print_info "- libffi-dev/libffi-devel"
            print_info "- libssl-dev/openssl-devel"
            print_info "- git, curl"
        fi
    elif [[ "$OS" == "macos" ]]; then
        print_info "Detected macOS system"
        
        # Check for Homebrew
        if ! command -v brew &> /dev/null; then
            print_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        print_info "Installing dependencies with Homebrew..."
        brew install libpcap git curl
        
        # Install Xcode command line tools if not present
        if ! xcode-select -p &> /dev/null; then
            print_info "Installing Xcode command line tools..."
            xcode-select --install
        fi
    fi
}

create_virtual_environment() {
    print_step "Creating virtual environment..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    $PYTHON_CMD -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    print_info "Virtual environment created at $INSTALL_DIR/venv"
}

download_framework() {
    print_step "Downloading framework..."
    
    if [[ -d "$INSTALL_DIR/advanced-ddos-framework" ]]; then
        print_info "Framework directory exists, updating..."
        cd "$INSTALL_DIR/advanced-ddos-framework"
        git pull
    else
        print_info "Cloning framework repository..."
        cd "$INSTALL_DIR"
        git clone "$REPO_URL" advanced-ddos-framework
    fi
}

install_framework() {
    print_step "Installing framework..."
    
    cd "$INSTALL_DIR/advanced-ddos-framework"
    
    # Activate virtual environment
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Install framework
    pip install -e .
    
    print_info "Framework installed successfully"
}

create_launcher_scripts() {
    print_step "Creating launcher scripts..."
    
    # Create bin directory
    mkdir -p "$INSTALL_DIR/bin"
    
    # Create main launcher
    cat > "$INSTALL_DIR/bin/ddos-framework" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.ddos-framework"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR/advanced-ddos-framework"
python ddos.py "$@"
EOF
    
    # Create CLI launcher
    cat > "$INSTALL_DIR/bin/ddos-cli" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.ddos-framework"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR/advanced-ddos-framework"
python -m core.interfaces.cli "$@"
EOF
    
    # Create web GUI launcher
    cat > "$INSTALL_DIR/bin/ddos-web" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.ddos-framework"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR/advanced-ddos-framework"
python -m core.interfaces.web_gui "$@"
EOF
    
    # Create API launcher
    cat > "$INSTALL_DIR/bin/ddos-api" << 'EOF'
#!/bin/bash
INSTALL_DIR="$HOME/.ddos-framework"
source "$INSTALL_DIR/venv/bin/activate"
cd "$INSTALL_DIR/advanced-ddos-framework"
python -m core.interfaces.api "$@"
EOF
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/bin/"*
    
    print_info "Launcher scripts created in $INSTALL_DIR/bin/"
}

setup_shell_integration() {
    print_step "Setting up shell integration..."
    
    # Add to PATH
    SHELL_RC=""
    if [[ "$SHELL" == *"bash"* ]]; then
        SHELL_RC="$HOME/.bashrc"
    elif [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ "$SHELL" == *"fish"* ]]; then
        SHELL_RC="$HOME/.config/fish/config.fish"
    fi
    
    if [[ -n "$SHELL_RC" && -f "$SHELL_RC" ]]; then
        # Check if already added
        if ! grep -q "ddos-framework" "$SHELL_RC"; then
            echo "" >> "$SHELL_RC"
            echo "# Advanced DDoS Framework" >> "$SHELL_RC"
            echo "export PATH=\"\$HOME/.ddos-framework/bin:\$PATH\"" >> "$SHELL_RC"
            print_info "Added to PATH in $SHELL_RC"
        else
            print_info "Already added to PATH"
        fi
    else
        print_warning "Could not detect shell configuration file."
        print_info "Please add $INSTALL_DIR/bin to your PATH manually."
    fi
}

run_tests() {
    print_step "Running basic tests..."
    
    cd "$INSTALL_DIR/advanced-ddos-framework"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Run quick validation
    if python -c "import core; print('Framework import successful')"; then
        print_success "Framework import test passed"
    else
        print_error "Framework import test failed"
        return 1
    fi
    
    # Test CLI
    if python ddos.py --help > /dev/null 2>&1; then
        print_success "CLI test passed"
    else
        print_error "CLI test failed"
        return 1
    fi
}

print_completion_message() {
    echo
    print_success "Installation completed successfully!"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    echo "2. Test the installation: ddos-framework --help"
    echo "3. Start the web interface: ddos-web"
    echo "4. Read the documentation: $INSTALL_DIR/advanced-ddos-framework/README.md"
    echo
    echo -e "${YELLOW}Important:${NC}"
    echo "- This framework is for educational and authorized testing only"
    echo "- Always ensure you have permission before testing any systems"
    echo "- Use only in controlled, isolated environments"
    echo
    echo -e "${BLUE}Support:${NC}"
    echo "- Documentation: https://ddos-framework.readthedocs.io/"
    echo "- Issues: https://github.com/ddos-framework/advanced-ddos-framework/issues"
    echo "- Email: support@ddos-framework.org"
    echo
}

# Main installation process
main() {
    print_header
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "Do not run this script as root!"
        print_info "The script will prompt for sudo when needed."
        exit 1
    fi
    
    # Installation steps
    check_os
    check_python
    check_pip
    install_system_dependencies
    create_virtual_environment
    download_framework
    install_framework
    create_launcher_scripts
    setup_shell_integration
    run_tests
    print_completion_message
}

# Handle interruption
trap 'echo -e "\n${RED}Installation interrupted!${NC}"; exit 1' INT

# Run main function
main "$@"