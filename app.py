import sys
import os

# Get absolute paths
current_dir = os.path.dirname(os.path.abspath(__file__))
nested_app_dir = os.path.join(current_dir, "agriculture--main")

# Remove current directory from sys.path to prevent importing ourselves circularly
sys.path = [path for path in sys.path if path not in (current_dir, "")]

# Add the nested folder containing the actual app.py
sys.path.insert(0, nested_app_dir)

# Import the actual Flask app from agriculture--main/app.py
from app import app
