#!/usr/bin/env python3
"""
Test runner script for the Morpheus application.
Runs comprehensive tests using testcontainers for database isolation.
"""

import subprocess
import sys
import os


def run_tests():
    """Run all tests with proper environment setup"""

    # Set test environment variables
    os.environ["TESTING"] = "1"
    os.environ["LOG_LEVEL"] = "WARNING"

    # Install test dependencies
    print("Installing test dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"],
        check=True,
    )

    # Run tests
    print("Running tests...")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        "--disable-warnings",
    ]

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
