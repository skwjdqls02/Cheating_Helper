
import subprocess
import sys
import os

def install_system_dependencies():
    """Installs system-level dependencies required for the Python packages on Ubuntu."""
    if os.geteuid() != 0:
        print("This script requires root privileges to install system dependencies. Please run with sudo.")
        # sys.exit(1) # Exit if not root, but for now we'll just print a warning.

    print("Updating package list...")
    try:
        subprocess.check_call(["apt-get", "update", "-y"])
    except subprocess.CalledProcessError as e:
        print(f"Failed to update package list. Error: {e}")
        return False

    print("Installing system dependencies...")
    system_packages = [
        "libgl1-mesa-glx",
        "libglib2.0-0",
        "libsm6",
        "libxext6",
        "libxrender-dev",
        "python3-pip" # Ensure pip is installed
    ]
    try:
        subprocess.check_call(["apt-get", "install", "-y"] + system_packages)
        print("System dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install system dependencies. Error: {e}")
        return False

def install_package(package):
    """Checks if a package is installed and installs it if not."""
    try:
        # For packages with different import names
        if package == "opencv-python-headless":
            __import__("cv2")
        elif package == "python-multipart":
             __import__("multipart")
        else:
            __import__(package)
        print(f"{package} is already installed.")
    except ImportError:
        print(f"{package} not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} has been successfully installed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}. Error: {e}")


if __name__ == "__main__":
    # First, install system dependencies
    if "linux" in sys.platform:
        print("Detected Linux environment. Installing system dependencies...")
        if not install_system_dependencies():
            print("Could not install system dependencies. Python package installation might fail.")
    
    # Python packages required for the server
    # Using opencv-python-headless as it's better for server environments (no GUI dependencies)
    required_packages = [
        "fastapi", 
        "uvicorn[standard]", 
        "easyocr", 
        "opencv-python-headless", 
        "openai", 
        "torch", 
        "torchvision", 
        "python-multipart"
    ]
    
    print("\nInstalling Python packages...")
    for package in required_packages:
        install_package(package)

    print("\nDependency installation process finished.")
