#!/bin/bash

echo "===================================="
echo "DSS DASHBOARD LAUNCHER"
echo "===================================="
echo ""
echo "Starting Streamlit dashboard..."
echo "Dashboard will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo "===================================="
echo ""

streamlit run dss_system/visualization/streamlit_app.py
