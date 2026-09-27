"""
Pytest configuration for FoodLoop AI backend tests.
Prevents Windows Python 3.13 pyarrow DLL entry point issue by ensuring pandas uses NumPy.
"""
import sys

# Prevent Windows fatal exception 0xc0000139 in pyarrow DLL
sys.modules["pyarrow"] = None
