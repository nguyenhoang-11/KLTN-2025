"""
Launch Streamlit Dashboard
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Get dashboard path
    dashboard_path = Path(__file__).parent.parent / "dss_system" / "visualization" / "streamlit_app.py"

    print("="*60)
    print("LAUNCHING DSS DASHBOARD")
    print("="*60)
    print(f"\nDashboard will open at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the server")
    print("="*60)

    # Launch streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port=8501",
        "--server.headless=false",
        "--browser.gatherUsageStats=false"
    ])


if __name__ == "__main__":
    main()
