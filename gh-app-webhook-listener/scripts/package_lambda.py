#!/usr/bin/env python3
"""
Package Lambda functions with their specific dependencies.
This script creates optimized packages for each Lambda function.
Compatible with the new separated directory structure.
"""
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"


def clean_build_directory():
    """Clean build directory."""
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(exist_ok=True)


def install_dependencies(requirements_file: Path, target_dir: Path):
    """Install dependencies to target directory."""
    if requirements_file.exists():
        print(f"  Installing dependencies from {requirements_file.name}")
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", str(requirements_file),
            "-t", str(target_dir),
            "--platform", "manylinux2014_x86_64",
            "--only-binary", ":all:",
            "--upgrade"
        ], check=True)
    else:
        print(f"  No requirements.txt found")


def package_lambda(function_name: str):
    """Package a Lambda function with its dependencies."""
    print(f"\n=== Packaging {function_name} ===")

    # Create build directory for this Lambda
    function_build_dir = BUILD_DIR / f"{function_name}_build"
    if function_build_dir.exists():
        shutil.rmtree(function_build_dir)
    function_build_dir.mkdir(parents=True)

    # Copy Lambda-specific code
    lambda_src = SRC_DIR / function_name
    if lambda_src.exists():
        shutil.copytree(lambda_src, function_build_dir / function_name)
        print(f"  Copied {function_name} code")
    else:
        print(f"  ERROR: {lambda_src} not found")
        return None

    # Copy common utilities
    common_src = SRC_DIR / "common"
    if common_src.exists():
        shutil.copytree(common_src, function_build_dir / "common")
        print(f"  Copied common utilities")

    # Install dependencies from Lambda-specific requirements
    requirements = lambda_src / "requirements.txt"
    install_dependencies(requirements, function_build_dir)

    # Create ZIP file
    zip_path = BUILD_DIR / f"{function_name}.zip"
    print(f"  Creating {zip_path.name}...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(function_build_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']

            for file in files:
                # Skip compiled files
                if file.endswith('.pyc'):
                    continue

                file_path = Path(root) / file
                arcname = file_path.relative_to(function_build_dir)
                zipf.write(file_path, arcname)

    # Get size in MB
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Created {zip_path.name} ({size_mb:.2f} MB)")

    # Show package contents summary
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        namelist = zipf.namelist()
        dirs = {}
        for name in namelist:
            if '/' in name:
                dir_name = name.split('/')[0]
                dirs[dir_name] = dirs.get(dir_name, 0) + 1
            else:
                dirs['root'] = dirs.get('root', 0) + 1

        print("  Package contents:")
        for dir_name, count in sorted(dirs.items()):
            print(f"    {dir_name}: {count} files")

    return zip_path


def main():
    """Main packaging function."""
    print("Lambda Packaging Script")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Source directory: {SRC_DIR}")

    # Clean build directory
    clean_build_directory()

    # Package both Lambda functions
    functions = ["webhook_handler", "check_processor"]
    success = True

    for func in functions:
        try:
            zip_path = package_lambda(func)
            if zip_path:
                print(f"[OK] Successfully packaged {func}")
            else:
                print(f"[FAIL] Failed to package {func}")
                success = False
        except Exception as e:
            print(f"[ERROR] Error packaging {func}: {e}")
            success = False

    if success:
        print("\n=== All Lambda functions packaged successfully! ===")
        return 0
    else:
        print("\n=== Some Lambda functions failed to package ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())