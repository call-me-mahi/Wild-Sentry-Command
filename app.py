import sys
import os

# Add the agriculture--main directory to the system path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agriculture--main"))

# Import the actual Flask app from agriculture--main/app.py
from app import app
