"""
Python interpreter startup hook for Harvest Harbor backend.
Automatically configures KERAS_HOME before any TensorFlow/Keras import fires,
preventing PermissionError in sandboxed environments without requiring manual env vars.
"""
import os
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
if "KERAS_HOME" not in os.environ:
    os.environ["KERAS_HOME"] = str(_BACKEND_DIR / ".keras")
