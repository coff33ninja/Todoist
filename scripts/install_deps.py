import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install or update project dependencies"""
    try:
        # Get the project root directory (where requirements.txt is located)
        project_root = Path(__file__).parent.parent
        requirements_file = project_root / "requirements.txt"
        
        if not requirements_file.exists():
            print("Error: requirements.txt not found!")
            return False

        print("Uninstalling potentially conflicting packages...")
        # Uninstall packages that might conflict
        packages_to_clean = [
            "flask",
            "flask-cors",
            "Werkzeug",
            "click",
            "itsdangerous",
            "Jinja2"
        ]
        
        for package in packages_to_clean:
            try:
                subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package],
                             check=True)
                print(f"Successfully uninstalled {package}")
            except subprocess.CalledProcessError:
                print(f"Note: {package} was not installed")
            except Exception as e:
                print(f"Warning: Error while uninstalling {package}: {e}")

        print("\nInstalling dependencies from requirements.txt...")
        # Install all requirements
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:", result.stderr)

        # Verify Flask installation
        print("\nVerifying Flask installation...")
        verify_result = subprocess.run(
            [sys.executable, "-c", "import flask; print(f'Flask version: {flask.__version__}')"],
            capture_output=True,
            text=True
        )
        if verify_result.returncode == 0:
            print(verify_result.stdout.strip())
            return True
        else:
            print("Warning: Flask verification failed!")
            print(verify_result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error during dependency installation: {e}")
        if e.output:
            print(e.output)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    if install_dependencies():
        print("\nDependencies installed successfully!")
    else:
        print("\nError occurred during dependency installation.")
        sys.exit(1)