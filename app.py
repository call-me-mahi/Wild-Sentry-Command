import sys
import os

# Get absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
nested_app_dir = os.path.join(current_dir, "agriculture--main")

# Remove current directory from path list to prevent importing ourselves
sys.path = [path for path in sys.path if path not in (current_dir, "")]

# Add the nested folder containing the actual app.py
sys.path.insert(0, nested_app_dir)

# Remove the cached root 'app' module from sys.modules to clear the circular reference
if "app" in sys.modules:
    del sys.modules["app"]

# Import the actual Flask app from the nested app.py
import app
from app import app
