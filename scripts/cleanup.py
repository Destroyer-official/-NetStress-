#!/usr/bin/env python3
"""
NetStress Project Cleanup Script

Moves unnecessary files to the unnecessary/ folder and cleans up the project.
"""

import os
import shutil
import sys
from pathlib import Path

# Files/patterns to move to unnecessary/
UNNECESSARY_PATTERNS = [
    # Log files
    "attack.log",
    "*.log",
    
    # Test result files in root
    "test_*.txt",
    "test_*.json",
    "*_results.txt",
    "*_results.json",
    "*_report*.txt",
    "*_report*.json",
    
    # Old benchmark files
    "benchmark_*.txt",
    "benchmark_*.json",
    
    # Checkpoint files
    "checkpoint_*.py",
    "*_summary.py",
    
    # Old test runners (not in tests/)
    "*_runner.py",
    "*_test.py",
]

# Directories to move to unnecessary/
UNNECESSARY_DIRS = [
    "benchmark_reports",
    "compliance_reports",
    "regression_reports",
    "validation_reports",
    "demo_audit_logs",
]

# Files to keep in root
KEEP_FILES = [
    "ddos.py",
    "main.py",
    "netstress_cli.py",
    "benchmark_comparison.py",
    "requirements.txt",
    "setup.py",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CAPABILITIES.md",
    "ENHANCEMENTS.md",
    "PROJECT_STRUCTURE.md",
    "PRODUCTION_CHECKLIST.md",
    "PERFORMANCE_BENCHMARK.md",
    "REAL_IMPLEMENTATION_NOTICE.md",
    "MANIFEST.in",
    "netstress.json",
    "performance_thresholds.json",
    ".gitignore",
    ".gitattributes",
]


def cleanup_project(project_root: str, dry_run: bool = True):
    """Clean up the project by moving unnecessary files."""
    
    root = Path(project_root)
    unnecessary_dir = root / "unnecessary"
    
    # Create unnecessary directory if it doesn't exist
    unnecessary_dir.mkdir(exist_ok=True)
    
    moved_files = []
    moved_dirs = []
    
    # Move unnecessary directories
    for dir_name in UNNECESSARY_DIRS:
        dir_path = root / dir_name
        if dir_path.exists() and dir_path.is_dir():
            dest = unnecessary_dir / dir_name
            if dry_run:
                print(f"[DRY RUN] Would move directory: {dir_path} -> {dest}")
            else:
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(dir_path), str(dest))
                print(f"Moved directory: {dir_path} -> {dest}")
            moved_dirs.append(dir_name)
    
    # Move unnecessary files
    for item in root.iterdir():
        if item.is_file():
            name = item.name
            
            # Skip files we want to keep
            if name in KEEP_FILES:
                continue
            
            # Check if file matches unnecessary patterns
            should_move = False
            for pattern in UNNECESSARY_PATTERNS:
                if pattern.startswith("*"):
                    if name.endswith(pattern[1:]):
                        should_move = True
                        break
                elif pattern.endswith("*"):
                    if name.startswith(pattern[:-1]):
                        should_move = True
                        break
                elif name == pattern:
                    should_move = True
                    break
            
            if should_move:
                dest = unnecessary_dir / name
                if dry_run:
                    print(f"[DRY RUN] Would move file: {item} -> {dest}")
                else:
                    shutil.move(str(item), str(dest))
                    print(f"Moved file: {item} -> {dest}")
                moved_files.append(name)
    
    # Clean up __pycache__ directories
    for pycache in root.rglob("__pycache__"):
        if "unnecessary" not in str(pycache):
            if dry_run:
                print(f"[DRY RUN] Would remove: {pycache}")
            else:
                shutil.rmtree(pycache)
                print(f"Removed: {pycache}")
    
    # Clean up .pyc files
    for pyc in root.rglob("*.pyc"):
        if "unnecessary" not in str(pyc):
            if dry_run:
                print(f"[DRY RUN] Would remove: {pyc}")
            else:
                pyc.unlink()
                print(f"Removed: {pyc}")
    
    print(f"\nSummary:")
    print(f"  Directories moved: {len(moved_dirs)}")
    print(f"  Files moved: {len(moved_files)}")
    
    if dry_run:
        print("\n[DRY RUN] No changes made. Run with --execute to apply changes.")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up NetStress project")
    parser.add_argument("--execute", action="store_true", help="Actually move files (default is dry run)")
    parser.add_argument("--root", default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    # Find project root
    root = Path(args.root).resolve()
    if not (root / "ddos.py").exists():
        print(f"Error: {root} does not appear to be the NetStress project root")
        sys.exit(1)
    
    print(f"Cleaning up project at: {root}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    print()
    
    cleanup_project(str(root), dry_run=not args.execute)


if __name__ == "__main__":
    main()
