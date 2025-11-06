
import subprocess
import sys

def install_package(package):
    """Checks if a package is installed and installs it if not."""
    try:
        __import__(package)
        print(f"{package} is already installed.")
    except ImportError:
        print(f"{package} not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} has been successfully installed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}. Error: {e}")
            # For opencv-python, the import name is cv2
            if package == "cv2":
                install_package("opencv-python")


if __name__ == "__main__":
    # Add torch and torchvision as they are dependencies for easyocr
    required_packages = ["fastapi", "uvicorn[standard]", "easyocr", "opencv-python", "openai", "torch", "torchvision", "python-multipart"]
    for package in required_packages:
        # Special handling for packages with different import names
        if package == "opencv-python":
            install_package("cv2")
        else:
            install_package(package)
