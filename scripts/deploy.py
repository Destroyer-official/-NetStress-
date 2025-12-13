#!/usr/bin/env python3
"""
NetStress 2.0 Production Deployment Script

Handles installation, configuration, and deployment for production environments.
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_status(msg: str, status: str = "info"):
    """Print colored status message"""
    colors = {
        "info": Colors.BLUE,
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED
    }
    color = colors.get(status, Colors.BLUE)
    symbol = {"info": "ℹ", "success": "✓", "warning": "⚠", "error": "✗"}.get(status, "•")
    print(f"{color}{symbol}{Colors.END} {msg}")


def run_command(cmd: List[str], cwd: Optional[str] = None) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            timeout=300
        )
        return result.returncode == 0
    except Exception as e:
        print_status(f"Command failed: {e}", "error")
        return False


def check_python_version() -> bool:
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_status(f"Python 3.8+ required, found {version.major}.{version.minor}", "error")
        return False
    print_status(f"Python {version.major}.{version.minor}.{version.micro}", "success")
    return True


def check_dependencies() -> bool:
    """Check and install dependencies"""
    print_status("Checking dependencies...")
    
    required = [
        "psutil",
        "asyncio",
        "aiohttp",
    ]
    
    missing = []
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print_status(f"Installing missing: {', '.join(missing)}", "warning")
        if not run_command([sys.executable, "-m", "pip", "install"] + missing):
            return False
    
    print_status("All dependencies available", "success")
    return True


def install_requirements(project_dir: Path) -> bool:
    """Install requirements from requirements.txt"""
    req_file = project_dir / "requirements.txt"
    if not req_file.exists():
        print_status("requirements.txt not found", "warning")
        return True
    
    print_status("Installing requirements...")
    if run_command([sys.executable, "-m", "pip", "install", "-r", str(req_file)]):
        print_status("Requirements installed", "success")
        return True
    return False


def check_rust() -> bool:
    """Check if Rust is installed"""
    if shutil.which("cargo"):
        print_status("Rust toolchain found", "success")
        return True
    print_status("Rust not found (optional for native engine)", "warning")
    return False


def build_native_engine(project_dir: Path) -> bool:
    """Build the native Rust engine"""
    rust_dir = project_dir / "native" / "rust_engine"
    if not rust_dir.exists():
        print_status("Native engine source not found", "warning")
        return False
    
    if not check_rust():
        print_status("Skipping native engine build (Rust not installed)", "warning")
        return False
    
    # Check for maturin
    if not shutil.which("maturin"):
        print_status("Installing maturin...")
        if not run_command([sys.executable, "-m", "pip", "install", "maturin"]):
            return False
    
    print_status("Building native engine...")
    if run_command(["maturin", "develop", "--release"], cwd=str(rust_dir)):
        print_status("Native engine built successfully", "success")
        return True
    
    print_status("Native engine build failed (will use Python fallback)", "warning")
    return False


def create_config(project_dir: Path, environment: str = "production") -> bool:
    """Create production configuration"""
    config_file = project_dir / "netstress.json"
    
    config = {
        "environment": environment,
        "version": "2.0.0",
        "safety": {
            "enable_target_validation": True,
            "max_rate_pps": 10000000,
            "max_duration_seconds": 3600,
            "enable_audit_logging": True,
            "require_confirmation": environment == "production"
        },
        "performance": {
            "use_native_engine": True,
            "use_zero_copy": True,
            "thread_count": 0,  # Auto-detect
            "buffer_size": 65536
        },
        "logging": {
            "level": "INFO" if environment == "production" else "DEBUG",
            "format": "json" if environment == "production" else "text",
            "file": "netstress.log",
            "max_size_mb": 100,
            "backup_count": 5
        },
        "health": {
            "enable_self_healing": True,
            "check_interval_seconds": 10,
            "memory_threshold_percent": 80,
            "cpu_threshold_percent": 85
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_status(f"Configuration created: {config_file}", "success")
    return True


def run_tests(project_dir: Path) -> bool:
    """Run the test suite"""
    print_status("Running tests...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        # Count passed tests
        lines = result.stdout.split('\n')
        for line in lines:
            if 'passed' in line:
                print_status(line.strip(), "success")
                break
        return True
    else:
        print_status("Some tests failed", "warning")
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        return False


def verify_installation(project_dir: Path) -> bool:
    """Verify the installation works"""
    print_status("Verifying installation...")
    
    # Try to import core modules
    sys.path.insert(0, str(project_dir))
    
    try:
        from core import __version__
        print_status(f"NetStress version: {__version__}", "success")
    except ImportError as e:
        print_status(f"Import error: {e}", "error")
        return False
    
    # Try CLI status
    result = subprocess.run(
        [sys.executable, "netstress_cli.py", "--status"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print_status("CLI working", "success")
        return True
    
    print_status("CLI check failed", "warning")
    return True  # Non-fatal


def print_summary(results: Dict[str, bool]):
    """Print deployment summary"""
    print("\n" + "="*50)
    print(f"{Colors.BOLD}Deployment Summary{Colors.END}")
    print("="*50)
    
    for step, success in results.items():
        status = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
        print(f"  {status} {step}")
    
    all_success = all(results.values())
    critical_success = results.get("python_version", False) and results.get("dependencies", False)
    
    print("="*50)
    if all_success:
        print(f"{Colors.GREEN}{Colors.BOLD}Deployment successful!{Colors.END}")
    elif critical_success:
        print(f"{Colors.YELLOW}{Colors.BOLD}Deployment completed with warnings{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}Deployment failed{Colors.END}")
    
    print("\nNext steps:")
    print("  1. Review configuration: netstress.json")
    print("  2. Check status: python netstress_cli.py --status")
    print("  3. Run dry test: python netstress_cli.py -t 127.0.0.1 -p 80 -P UDP --dry-run")


def main():
    parser = argparse.ArgumentParser(description="NetStress 2.0 Deployment")
    parser.add_argument("--env", choices=["development", "staging", "production"],
                       default="production", help="Deployment environment")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-native", action="store_true", help="Skip native engine build")
    parser.add_argument("--project-dir", type=str, help="Project directory")
    
    args = parser.parse_args()
    
    # Determine project directory
    if args.project_dir:
        project_dir = Path(args.project_dir)
    else:
        project_dir = Path(__file__).parent.parent
    
    print(f"\n{Colors.BOLD}NetStress 2.0 Deployment{Colors.END}")
    print(f"Environment: {args.env}")
    print(f"Project: {project_dir}\n")
    
    results = {}
    
    # Step 1: Check Python
    results["python_version"] = check_python_version()
    if not results["python_version"]:
        print_summary(results)
        return 1
    
    # Step 2: Check dependencies
    results["dependencies"] = check_dependencies()
    
    # Step 3: Install requirements
    results["requirements"] = install_requirements(project_dir)
    
    # Step 4: Build native engine (optional)
    if not args.skip_native:
        results["native_engine"] = build_native_engine(project_dir)
    else:
        results["native_engine"] = True
        print_status("Skipping native engine build", "info")
    
    # Step 5: Create configuration
    results["configuration"] = create_config(project_dir, args.env)
    
    # Step 6: Run tests (optional)
    if not args.skip_tests:
        results["tests"] = run_tests(project_dir)
    else:
        results["tests"] = True
        print_status("Skipping tests", "info")
    
    # Step 7: Verify installation
    results["verification"] = verify_installation(project_dir)
    
    print_summary(results)
    
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
