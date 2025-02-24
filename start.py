import argparse
import sys
import os

# Add root directory to Python path
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

import subprocess
import sys
import os

def start_application():
    """Start the Flask application"""
    print("Starting Todoist application...")
    # Set Python path before running the application
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    subprocess.run(["python", "core/main.py"], env=env)

def train_model():
    """Train the NLU model"""
    print("Training NLU model...")
    subprocess.run(["python", "scripts/train_nlu.py"])

def run_tests():
    """Run all tests"""
    print("Running tests...")
    subprocess.run(["pytest", "tests/"])

def add_data():
    """Add sample data to the database"""
    print("Adding sample data...")
    subprocess.run(["python", "utils/populate_test_data.py"])

def main():
    parser = argparse.ArgumentParser(description="Todoist Application Management")
    parser.add_argument("command", choices=["start", "train", "test", "add-data"],
                       help="Command to execute: start, train, test, or add-data")

    args = parser.parse_args()

    if args.command == "start":
        start_application()
    elif args.command == "train":
        train_model()
    elif args.command == "test":
        run_tests()
    elif args.command == "add-data":
        add_data()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
