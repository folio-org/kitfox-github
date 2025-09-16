#!/usr/bin/env python3
import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path

def package_lambda(function_name):
    """Package Lambda function with dependencies"""
    base_dir = Path(__file__).parent.parent
    src_dir = base_dir / "src"
    build_dir = base_dir / "build"

    # Clean and create build directory
    function_build_dir = build_dir / function_name
    if function_build_dir.exists():
        shutil.rmtree(function_build_dir)
    function_build_dir.mkdir(parents=True)

    # Copy source files
    print(f"Copying source files for {function_name}...")
    shutil.copytree(src_dir / "handlers", function_build_dir / "handlers")
    shutil.copytree(src_dir / "services", function_build_dir / "services")
    shutil.copytree(src_dir / "validators", function_build_dir / "validators")
    shutil.copytree(src_dir / "utils", function_build_dir / "utils")

    # Install dependencies
    print(f"Installing dependencies for {function_name}...")
    requirements_file = base_dir / "requirements.txt"
    if requirements_file.exists():
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "-r", str(requirements_file),
            "-t", str(function_build_dir),
            "--quiet"
        ], check=True)

    # Create zip file
    zip_path = build_dir / f"{function_name}.zip"
    print(f"Creating {zip_path}...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(function_build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(function_build_dir)
                zipf.write(file_path, arcname)

    print(f"Created {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")
    return zip_path

def main():
    print("Packaging Lambda functions...")

    # Package both Lambda functions
    functions = ["webhook_handler", "check_processor"]

    for func in functions:
        try:
            package_lambda(func)
            print(f"[OK] Packaged {func}")
        except Exception as e:
            print(f"[FAIL] Error packaging {func}: {e}")
            sys.exit(1)

    print("\nAll Lambda functions packaged successfully!")

if __name__ == "__main__":
    main()