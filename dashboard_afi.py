"""
AFI Dashboard Launcher
Launch the AFI Enterprise Data dashboard

Usage:
    python dashboard_afi.py
"""

import os
import sys

# Change to project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Add to path
sys.path.insert(0, os.getcwd())

# Run streamlit
os.system("streamlit run dss_system/visualization/streamlit_app_afi.py")
