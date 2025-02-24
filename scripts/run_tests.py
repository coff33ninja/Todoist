import subprocess
import sys
import os
from pathlib import Path
import argparse
import time
import json

class TestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.start_time = None
        self.end_time = None

    def print_header(self, message):
        """Print a formatted header"""
        print("\n" + "=" * 80)
        print(f" {message} ".center(80, "="))
        print("=" * 80 + "\n")

    def print_section(self, message):
        """Print a section header"""
        print("\n" + "-" * 40)
        print(f" {message} ")
        print("-" * 40 + "\n")

    def run_command(self, command, description):
        """Run a command and handle its output"""
        try:
            self.print_section(description)
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(self.project_root)
            )
            
            # Print stdout if there is any
            if result.stdout:
                print(result.stdout)
            
            # Print stderr if there is any
            if result.stderr:
                print("Warnings/Errors:")
                print(result.stderr)
            
            return result.returncode == 0
        except Exception as e:
            print(f"Error running {description}: {e}")
            return False

    def verify_test_environment(self):
        """Verify that the test environment is properly set up"""
        self.print_section("Verifying test environment")
        
        # Check if pytest is installed
        try:
            import pytest
            print(f"✓ pytest version {pytest.__version__} is installed")
        except ImportError:
            print("✗ pytest is not installed!")
            return False

        # Check if test directory exists
        if not self.test_dir.exists():
            print("✗ Test directory not found!")
            return False
        print("✓ Test directory found")

        # Check for test files
        test_files = list(self.test_dir.glob("test_*.py"))
        if not test_files:
            print("✗ No test files found!")
            return False
        print(f"✓ Found {len(test_files)} test files:")
        for test_file in test_files:
            print(f"  - {test_file.name}")

        return True

    def run_tests(self, args):
        """Run the tests based on provided arguments"""
        self.start_time = time.time()
        
        if not self.verify_test_environment():
            print("\n❌ Test environment verification failed!")
            return False

        success = True
        
        # Base pytest command
        pytest_cmd = [sys.executable, "-m", "pytest"]
        
        # Add verbosity
        if args.verbose:
            pytest_cmd.append("-v")
        
        # Add coverage if requested
        if args.coverage:
            pytest_cmd.extend(["--cov=.", "--cov-report=term-missing"])
        
        # Add specific test file if provided
        if args.test_file:
            test_path = self.test_dir / args.test_file
            if not test_path.exists():
                print(f"\n❌ Test file not found: {args.test_file}")
                return False
            pytest_cmd.append(str(test_path))
        
        # Add specific test function if provided
        if args.test_function:
            pytest_cmd.append(f"-k {args.test_function}")

        # Run the tests
        success = self.run_command(pytest_cmd, "Running tests")

        self.end_time = time.time()
        self.print_summary(success)
        
        return success

    def print_summary(self, success):
        """Print a summary of the test run"""
        duration = self.end_time - self.start_time
        
        self.print_header("Test Run Summary")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Status: {'✅ Passed' if success else '❌ Failed'}")

def write_lint_errors(errors, output_file="lint_errors.json"):
    """Write linting errors to a JSON file"""
    try:
        with open(output_file, "w") as f:
            json.dump(errors, f, indent=2)
        print(f"Lint errors written to {output_file}")
    except Exception as e:
        print(f"Error writing lint errors: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run project tests with various options")
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="Enable verbose output")
    parser.add_argument("-c", "--coverage", action="store_true",
                        help="Run tests with coverage report")
    parser.add_argument("-f", "--test-file", type=str,
                        help="Run specific test file (e.g., test_nlu_processor.py)")
    parser.add_argument("-t", "--test-function", type=str,
                        help="Run specific test function (e.g., test_inventory_query)")
    parser.add_argument("-l", "--lint-output", type=str,
                        help="Output file for lint errors (default: lint_errors.json)")
    
    args = parser.parse_args()
    
    # Define the lint errors
    lint_errors = [
        {
            "resource": str(Path(__file__).resolve()),
            "owner": "Ruff",
            "code": {
                "value": "F401",
                "target": {
                    "$mid": 1,
                    "path": "/ruff/rules/unused-import",
                    "scheme": "https",
                    "authority": "docs.astral.sh"
                }
            },
            "severity": 4,
            "message": "`os` imported but unused",
            "source": "Ruff",
            "startLineNumber": 5,
            "startColumn": 8,
            "endLineNumber": 5,
            "endColumn": 10,
            "tags": [1]
        },
        {
            "resource": str(Path(__file__).resolve()),
            "owner": "Ruff",
            "code": {
                "value": "F401",
                "target": {
                    "$mid": 1,
                    "path": "/ruff/rules/unused-import",
                    "scheme": "https",
                    "authority": "docs.astral.sh"
                }
            },
            "severity": 4,
            "message": "`json` imported but unused",
            "source": "Ruff",
            "startLineNumber": 11,
            "startColumn": 8,
            "endLineNumber": 11,
            "endColumn": 12,
            "tags": [1]
        }
    ]
    
    # Write lint errors to file
    output_file = args.lint_output or "lint_errors.json"
    write_lint_errors(lint_errors, output_file)
    
    # Run tests
    runner = TestRunner()
    success = runner.run_tests(args)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()