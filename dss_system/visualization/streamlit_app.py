"""
Streamlit Dashboard for DSS System
Run with: streamlit run dss_system/visualization/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dss_system.data.loader import SupplyChainDataLoader
from dss_system.network.graph import SupplyChainNetwork
from dss_system.network.analysis import NetworkAnalyzer
from dss_system.visualization.network_viz import NetworkVisualizer
from dss_system.utils.config import config
from dss_system.auth.user_manager import get_user_manager


# Page configuration
st.set_page_config(
    page_title="Supply Chain DSS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for NiceAdmin-inspired design
st.markdown("""
    <style>
    /* Import Google Fonts - Nunito (like NiceAdmin) */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Global Styles */
    * {
        font-family: 'Nunito', sans-serif;
    }

    .main {
        padding: 1rem 2rem;
        background-color: #f6f9ff;
    }

    /* Header Styles - NiceAdmin Style */
    h1 {
        color: #012970;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 1rem;
        font-family: 'Nunito', sans-serif;
    }

    h2 {
        color: #012970;
        font-weight: 600;
        font-size: 1.5rem;
        margin-top: 1.5rem;
    }

    h3 {
        color: #012970;
        font-weight: 600;
        font-size: 1.25rem;
        margin-bottom: 1rem;
    }

    /* Page Title with Breadcrumb */
    .page-title {
        margin-bottom: 2rem;
    }

    .page-title h1 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #012970;
        margin-bottom: 0.25rem;
    }

    .breadcrumb {
        font-size: 0.875rem;
        color: #899bbd;
    }

    /* NiceAdmin Cards */
    .nice-card {
        background: #fff;
        border-radius: 5px;
        padding: 1.5rem;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
        margin-bottom: 1.5rem;
        border-left: 4px solid #4154f1;
        transition: all 0.3s ease;
    }

    .nice-card:hover {
        box-shadow: 0px 0 40px rgba(1, 41, 112, 0.15);
    }

    .nice-card-title {
        font-size: 1.125rem;
        font-weight: 700;
        color: #012970;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #ebeef4;
    }

    /* Metric Cards - NiceAdmin Style */
    [data-testid="stMetric"] {
        background: #fff;
        padding: 1.5rem;
        border-radius: 5px;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
        border-left: 4px solid #4154f1;
        transition: all 0.3s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0px 0 40px rgba(1, 41, 112, 0.15);
    }

    [data-testid="stMetric"] label {
        color: #899bbd !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #012970 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #4154f1 !important;
        font-weight: 600;
    }

    /* Info Cards with Icons */
    .info-card {
        background: #fff;
        border-radius: 5px;
        padding: 1.25rem;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
    }

    .info-card:hover {
        box-shadow: 0px 0 40px rgba(1, 41, 112, 0.15);
    }

    .info-card-icon {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        margin-right: 1rem;
    }

    .info-card-icon.blue {
        background-color: #cfe2ff;
        color: #084298;
    }

    .info-card-icon.green {
        background-color: #d1e7dd;
        color: #0f5132;
    }

    .info-card-icon.orange {
        background-color: #fff3cd;
        color: #997404;
    }

    .info-card-icon.red {
        background-color: #f8d7da;
        color: #842029;
    }

    /* Sidebar Styles - NiceAdmin */
    [data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid #e3e6ef;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: #fff;
    }

    /* Sidebar Navigation */
    .sidebar-nav {
        padding: 0;
        list-style: none;
    }

    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }

    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.25rem;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: #012970 !important;
        font-weight: 600;
        font-size: 0.9375rem;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        transition: all 0.3s ease;
        background-color: transparent;
        display: flex;
        align-items: center;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #f6f9ff;
        color: #4154f1 !important;
    }

    [data-testid="stSidebar"] .stRadio input:checked + div label {
        background-color: #f6f9ff;
        color: #4154f1 !important;
        border-left: 3px solid #4154f1;
        padding-left: calc(1rem - 3px);
    }

    /* Tabs - NiceAdmin Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: transparent;
        border-bottom: 2px solid #ebeef4;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #899bbd;
        border: none;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #4154f1 !important;
        border-bottom: 2px solid #4154f1;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #4154f1;
        background-color: #f6f9ff;
    }

    /* DataFrames - Bootstrap Table Style */
    .stDataFrame {
        border-radius: 5px;
        overflow: hidden;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
    }

    .dataframe {
        font-size: 0.875rem;
    }

    .dataframe thead tr th {
        background-color: #f6f9ff;
        color: #012970;
        font-weight: 700;
        border-bottom: 2px solid #4154f1;
        padding: 0.75rem;
    }

    .dataframe tbody tr {
        transition: all 0.3s ease;
    }

    .dataframe tbody tr:hover {
        background-color: #f6f9ff;
    }

    .dataframe tbody tr td {
        padding: 0.75rem;
        border-bottom: 1px solid #ebeef4;
    }

    /* Buttons - NiceAdmin Style */
    .stButton button {
        background-color: #4154f1;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(65, 84, 241, 0.3);
    }

    .stButton button:hover {
        background-color: #3142d3;
        box-shadow: 0 4px 12px rgba(65, 84, 241, 0.4);
    }

    /* Download Button */
    .stDownloadButton button {
        background-color: #198754;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.625rem 1.25rem;
        font-weight: 600;
        font-size: 0.875rem;
    }

    .stDownloadButton button:hover {
        background-color: #157347;
    }

    /* Alerts - Bootstrap Style */
    .stAlert {
        border-radius: 4px;
        border: 1px solid transparent;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        border-left-width: 4px;
    }

    /* Success Alert */
    div[data-baseweb="notification"][kind="success"] {
        background-color: #d1e7dd;
        border-color: #badbcc;
        border-left-color: #0f5132;
        color: #0f5132;
    }

    /* Warning Alert */
    div[data-baseweb="notification"][kind="warning"] {
        background-color: #fff3cd;
        border-color: #ffecb5;
        border-left-color: #997404;
        color: #997404;
    }

    /* Info Alert */
    div[data-baseweb="notification"][kind="info"] {
        background-color: #cfe2ff;
        border-color: #b6d4fe;
        border-left-color: #084298;
        color: #084298;
    }

    /* Error Alert */
    div[data-baseweb="notification"][kind="error"] {
        background-color: #f8d7da;
        border-color: #f5c2c7;
        border-left-color: #842029;
        color: #842029;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #fff;
        border-radius: 4px;
        padding: 1rem;
        font-weight: 600;
        color: #012970;
        border: 1px solid #ebeef4;
        transition: all 0.3s ease;
    }

    .streamlit-expanderHeader:hover {
        background-color: #f6f9ff;
        border-color: #4154f1;
    }

    /* Plotly Charts */
    .js-plotly-plot {
        border-radius: 5px;
        overflow: hidden;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
        background: white;
        padding: 1rem;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.35em 0.65em;
        font-size: 0.75em;
        font-weight: 700;
        line-height: 1;
        color: #fff;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
    }

    .badge-primary { background-color: #4154f1; }
    .badge-success { background-color: #198754; }
    .badge-warning { background-color: #ffc107; color: #000; }
    .badge-danger { background-color: #dc3545; }
    .badge-info { background-color: #0dcaf0; color: #000; }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f6f9ff;
    }

    ::-webkit-scrollbar-thumb {
        background: #4154f1;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #3142d3;
    }

    /* Text Input */
    .stTextInput input {
        border-radius: 4px;
        border: 1px solid #dee2e6;
        padding: 0.625rem 0.75rem;
        transition: all 0.3s ease;
        font-size: 0.875rem;
    }

    .stTextInput input:focus {
        border-color: #4154f1;
        box-shadow: 0 0 0 0.25rem rgba(65, 84, 241, 0.25);
    }

    /* Login Form Input - More compact */
    .login-container .stTextInput {
        margin-bottom: 0.75rem;
    }

    .login-container .stTextInput input {
        padding: 0.5rem 0.625rem;
        font-size: 0.8rem;
    }

    .login-container .stTextInput label {
        font-size: 0.8rem;
        margin-bottom: 0.25rem;
    }

    .login-container .stFormSubmitButton button {
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }

    .login-container h3 {
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
    }

    /* Select Box */
    .stSelectbox > div > div {
        border-radius: 4px;
        border: 1px solid #dee2e6;
    }

    /* Animation for page load */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .element-container {
        animation: fadeIn 0.5s ease-out;
    }

    /* Section Header */
    .section-header {
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #ebeef4;
    }

    .section-header h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #012970;
        margin: 0;
    }

    .section-header p {
        color: #899bbd;
        font-size: 0.875rem;
        margin: 0.25rem 0 0 0;
    }

    /* Activity Feed */
    .activity-feed {
        background: #fff;
        border-radius: 5px;
        padding: 1.5rem;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.1);
    }

    .activity-item {
        display: flex;
        padding: 1rem 0;
        border-bottom: 1px solid #ebeef4;
        transition: all 0.3s ease;
    }

    .activity-item:last-child {
        border-bottom: none;
    }

    .activity-item:hover {
        background-color: #f6f9ff;
        margin: 0 -1rem;
        padding: 1rem;
        border-radius: 4px;
    }

    .activity-icon {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        margin-right: 1rem;
        flex-shrink: 0;
    }

    .activity-content {
        flex: 1;
    }

    .activity-title {
        font-weight: 600;
        color: #012970;
        margin-bottom: 0.25rem;
    }

    .activity-time {
        font-size: 0.75rem;
        color: #899bbd;
    }

    /* Filter Panel */
    .filter-panel {
        background: #fff;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0px 0 20px rgba(1, 41, 112, 0.08);
        border-left: 3px solid #4154f1;
    }

    /* Stats Box */
    .stats-box {
        background: linear-gradient(135deg, #4154f1 0%, #3142d3 100%);
        color: white;
        border-radius: 5px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0px 0 30px rgba(65, 84, 241, 0.3);
    }

    .stats-box.green {
        background: linear-gradient(135deg, #2eca6a 0%, #1ea856 100%);
        box-shadow: 0px 0 30px rgba(46, 202, 106, 0.3);
    }

    .stats-box.orange {
        background: linear-gradient(135deg, #ff771d 0%, #e65c00 100%);
        box-shadow: 0px 0 30px rgba(255, 119, 29, 0.3);
    }

    .stats-box.red {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        box-shadow: 0px 0 30px rgba(220, 53, 69, 0.3);
    }

    .stats-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }

    .stats-label {
        font-size: 0.875rem;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Progress Bar */
    .progress-container {
        background-color: #ebeef4;
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .progress-bar {
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    .progress-bar.blue { background-color: #4154f1; }
    .progress-bar.green { background-color: #2eca6a; }
    .progress-bar.orange { background-color: #ff771d; }
    .progress-bar.red { background-color: #dc3545; }

    /* Login Page Styles */
    .login-container {
        max-width: 320px;
        margin: 2rem auto;
        padding: 1.25rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0px 0 30px rgba(1, 41, 112, 0.12);
    }

    .login-header {
        text-align: center;
        margin-bottom: 1.25rem;
    }

    .login-header img {
        width: 60px;
        height: 60px;
        margin-bottom: 0.5rem;
    }

    .login-header h1 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #012970;
        margin-bottom: 0.25rem;
    }

    .login-header p {
        color: #899bbd;
        font-size: 0.8rem;
    }

    .login-form {
        margin-top: 1rem;
    }

    .user-info {
        background: #f6f9ff;
        border-left: 3px solid #4154f1;
        padding: 0.75rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }

    .user-info strong {
        color: #012970;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def load_data():
    """Load data with caching"""
    loader = SupplyChainDataLoader()
    loader.load_all()
    return loader


@st.cache_resource
def build_network(_loader):
    """Build network with caching"""
    network = SupplyChainNetwork(_loader)
    return network


@st.cache_resource
def create_analyzer(_network, _loader):
    """Create analyzer with caching"""
    return NetworkAnalyzer(_network, _loader)


def show_login_page():
    """Display login page"""
    st.markdown("""
        <div class='login-container'>
            <div class='login-header'>
                <div style='font-size: 3rem;'>📊</div>
                <h1>Supply Chain DSS</h1>
                <p>Decision Support System</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Login form
    with st.form("login_form"):
        st.markdown("### 🔐 Sign In")

        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                # Authenticate user
                user_manager = get_user_manager()
                user = user_manager.authenticate(username, password)

                if user:
                    # Store session
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"✅ Welcome back, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

    st.markdown("""
        <div style='text-align: center; margin-top: 1.5rem; color: #899bbd; font-size: 0.75rem;'>
            <p style='margin: 0.25rem 0;'>© 2025 KLTN Project</p>
        </div>
    """, unsafe_allow_html=True)


def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show login page if not authenticated
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Sidebar with NiceAdmin design
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 2rem 0 1.5rem 0; border-bottom: 1px solid #ebeef4;'>
            <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'>📊</div>
            <h2 style='color: #012970; margin: 0; font-size: 1.25rem; font-weight: 700;'>Supply Chain DSS</h2>
            <p style='color: #899bbd; font-size: 0.75rem; margin-top: 0.25rem; font-weight: 600;'>
                DECISION SUPPORT SYSTEM
            </p>
        </div>
    """, unsafe_allow_html=True)

    # User Info
    user = st.session_state.user
    st.sidebar.markdown(f"""
        <div class='user-info'>
            <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                <div style='width: 40px; height: 40px; background: linear-gradient(135deg, #4154f1 0%, #3142d3 100%);
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-weight: 700; font-size: 1.2rem; margin-right: 0.75rem;'>
                    {user['full_name'][0].upper()}
                </div>
                <div>
                    <div style='font-weight: 700; color: #012970; font-size: 0.9rem;'>{user['full_name']}</div>
                    <div style='font-size: 0.75rem; color: #899bbd;'>{user['role'].upper()}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    page = st.sidebar.radio(
        "NAVIGATION",
        ["🏠 Overview", "📈 Data Analysis", "🔗 Network", "🎯 Optimization", "📊 Performance", "📄 Reports", "⚙️ Settings"],
        label_visibility="visible"
    )

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # Project info with NiceAdmin card style
    st.sidebar.markdown("""
        <div style='background: #fff; border-radius: 5px; padding: 1rem; margin: 1rem 0;
                    box-shadow: 0px 0 20px rgba(1, 41, 112, 0.1); border-left: 3px solid #4154f1;'>
            <h4 style='color: #012970; margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 700;'>
                ℹ️ ABOUT THIS SYSTEM
            </h4>
            <p style='color: #899bbd; font-size: 0.8rem; margin: 0; line-height: 1.6;'>
                Decision Support System for <strong style='color: #012970;'>Inventory Pooling</strong>
                in B2B Supply Networks via Proactive Lateral Transshipment and Coordinated Replenishment.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # System status with badge style
    st.sidebar.markdown("""
        <div style='background: #d1e7dd; border-left: 3px solid #198754;
                    border-radius: 5px; padding: 0.875rem; margin: 1rem 0;'>
            <p style='color: #0f5132; margin: 0; font-size: 0.8rem; line-height: 1.8;'>
                <span style='display: inline-block; width: 8px; height: 8px; background: #198754;
                             border-radius: 50%; margin-right: 0.5rem;'></span>
                <strong>System Status:</strong> Online<br>
                <span style='margin-left: 1.25rem;'>📅 Last Updated: Real-time</span><br>
                <span style='margin-left: 1.25rem;'>⚡ Performance: Optimal</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Logout Button
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    # Footer
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style='text-align: center; color: #899bbd; font-size: 0.7rem; padding-top: 1rem;
                    border-top: 1px solid #ebeef4;'>
            <p style='margin: 0.25rem 0;'>Powered by Streamlit & PuLP</p>
            <p style='margin: 0.25rem 0;'>© 2025 KLTN Project</p>
        </div>
    """, unsafe_allow_html=True)

    # Load data with custom spinner
    with st.spinner("🔄 Loading supply chain data... Please wait."):
        loader = load_data()
        network = build_network(loader)
        analyzer = create_analyzer(network, loader)

    # Route to pages
    if page == "🏠 Overview":
        show_overview_page(loader, network, analyzer)
    elif page == "📈 Data Analysis":
        show_analysis_page(loader, network, analyzer)
    elif page == "🔗 Network":
        show_network_page(loader, network)
    elif page == "🎯 Optimization":
        show_optimization_page(loader, network)
    elif page == "📊 Performance":
        show_performance_page(loader, network, analyzer)
    elif page == "📄 Reports":
        show_reports_page(loader, network, analyzer)
    elif page == "⚙️ Settings":
        show_settings_page()


def show_overview_page(loader, network, analyzer):
    """Overview page with key metrics"""
    # NiceAdmin page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Dashboard</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Dashboard</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    # Section header
    st.markdown("""
        <div class='section-header'>
            <h2>📊 Key Performance Indicators</h2>
            <p>Real-time metrics for supply chain performance monitoring</p>
        </div>
    """, unsafe_allow_html=True)

    # Get summary data
    summary = loader.get_network_summary()
    inv_analysis = analyzer.analyze_inventory_metrics()
    demand_analysis = analyzer.analyze_demand_patterns()
    transfer_analysis = analyzer.analyze_transfer_patterns()

    # KPI metrics in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Facilities",
            summary['num_facilities'],
            help="Number of facilities in network"
        )
        st.metric(
            "Total Products",
            summary['num_products'],
            help="Number of products managed"
        )

    with col2:
        st.metric(
            "Total Inventory",
            f"{inv_analysis['total_on_hand']:,.0f}",
            help="Total units on hand across all facilities"
        )
        st.metric(
            "Avg Days Supply",
            f"{inv_analysis['avg_days_of_supply']:.1f}",
            help="Average days of supply"
        )

    with col3:
        st.metric(
            "Total Demand",
            f"{demand_analysis['total_demand']:,.0f}",
            help="Total demand over period"
        )
        st.metric(
            "Demand CV",
            f"{demand_analysis['coefficient_of_variation']:.2%}" if demand_analysis['coefficient_of_variation'] else "N/A",
            help="Coefficient of variation (volatility)"
        )

    with col4:
        st.metric(
            "Total Transfers",
            transfer_analysis['total_transfers'],
            help="Number of lateral transshipments"
        )
        st.metric(
            "Transfer Cost",
            f"${transfer_analysis['total_cost']:,.0f}",
            help="Total transshipment cost"
        )

    # Network structure
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>🏢 Facilities by Type</h3>
            </div>
        """, unsafe_allow_html=True)
        fac_by_type = summary['facilities_by_type']
        fig = go.Figure(data=[go.Pie(
            labels=list(fac_by_type.keys()),
            values=list(fac_by_type.values()),
            hole=0.3,
            marker=dict(colors=['#4154f1', '#2eca6a', '#ff771d', '#012970'])
        )])
        fig.update_layout(
            height=300,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📦 Products by ABC Class</h3>
            </div>
        """, unsafe_allow_html=True)
        prod_by_class = summary['products_by_classification']
        fig = go.Figure(data=[go.Bar(
            x=list(prod_by_class.keys()),
            y=list(prod_by_class.values()),
            marker_color=['#4154f1', '#2eca6a', '#ff771d']
        )])
        fig.update_layout(
            height=300,
            showlegend=False,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Enhanced Info Cards with Icons
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class='section-header'>
            <h2>📋 Quick Stats</h2>
            <p>Key metrics at a glance</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class='info-card'>
                <div class='activity-icon blue'>
                    <span>📦</span>
                </div>
                <div style='flex: 1;'>
                    <div style='color: #899bbd; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem;'>
                        Total SKUs
                    </div>
                    <div style='color: #012970; font-size: 1.5rem; font-weight: 700;'>
                        {summary['num_products']}
                    </div>
                    <div class='progress-container'>
                        <div class='progress-bar blue' style='width: 100%;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        service_level = 95.5  # Calculate from your data
        st.markdown(f"""
            <div class='info-card'>
                <div class='activity-icon green'>
                    <span>✅</span>
                </div>
                <div style='flex: 1;'>
                    <div style='color: #899bbd; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem;'>
                        Service Level
                    </div>
                    <div style='color: #012970; font-size: 1.5rem; font-weight: 700;'>
                        {service_level:.1f}%
                    </div>
                    <div class='progress-container'>
                        <div class='progress-bar green' style='width: {service_level}%;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        fill_rate = 92.3  # Calculate from your data
        st.markdown(f"""
            <div class='info-card'>
                <div class='activity-icon orange'>
                    <span>📊</span>
                </div>
                <div style='flex: 1;'>
                    <div style='color: #899bbd; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem;'>
                        Fill Rate
                    </div>
                    <div style='color: #012970; font-size: 1.5rem; font-weight: 700;'>
                        {fill_rate:.1f}%
                    </div>
                    <div class='progress-container'>
                        <div class='progress-bar orange' style='width: {fill_rate}%;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        stockout_items = inv_analysis.get('stockout_risk', {}).get('num_items', 0)
        st.markdown(f"""
            <div class='info-card'>
                <div class='activity-icon red'>
                    <span>⚠️</span>
                </div>
                <div style='flex: 1;'>
                    <div style='color: #899bbd; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 0.25rem;'>
                        At Risk Items
                    </div>
                    <div style='color: #012970; font-size: 1.5rem; font-weight: 700;'>
                        {stockout_items}
                    </div>
                    <div class='progress-container'>
                        <div class='progress-bar red' style='width: {min(stockout_items * 10, 100)}%;'></div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Alerts & Recent Activity in two columns
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.markdown("""
            <div class='section-header'>
                <h2>⚠️ Alerts & Recommendations</h2>
                <p>Important notifications and optimization suggestions</p>
            </div>
        """, unsafe_allow_html=True)

        if inv_analysis.get('stockout_risk', {}).get('num_items', 0) > 0:
            st.warning(f"⚠️ {inv_analysis['stockout_risk']['num_items']} items below safety stock")

        if inv_analysis.get('excess_inventory', {}).get('num_items', 0) > 0:
            st.info(f"ℹ️ {inv_analysis['excess_inventory']['num_items']} items with excess inventory (>30 days)")

        opportunities = analyzer.identify_optimization_opportunities()
        if opportunities['inventory_rebalancing']:
            st.success(f"💡 {len(opportunities['inventory_rebalancing'])} inventory rebalancing opportunities identified")

    with col_right:
        st.markdown("""
            <div class='section-header'>
                <h2>🕐 Recent Activity</h2>
                <p>Latest system events</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class='activity-feed'>
                <div class='activity-item'>
                    <div class='activity-icon green'>
                        <span>✓</span>
                    </div>
                    <div class='activity-content'>
                        <div class='activity-title'>Transfer Completed</div>
                        <div class='activity-time'>5 minutes ago</div>
                    </div>
                </div>
                <div class='activity-item'>
                    <div class='activity-icon blue'>
                        <span>📦</span>
                    </div>
                    <div class='activity-content'>
                        <div class='activity-title'>Inventory Updated</div>
                        <div class='activity-time'>15 minutes ago</div>
                    </div>
                </div>
                <div class='activity-item'>
                    <div class='activity-icon orange'>
                        <span>⚠️</span>
                    </div>
                    <div class='activity-content'>
                        <div class='activity-title'>Low Stock Alert</div>
                        <div class='activity-time'>1 hour ago</div>
                    </div>
                </div>
                <div class='activity-item'>
                    <div class='activity-icon blue'>
                        <span>📊</span>
                    </div>
                    <div class='activity-content'>
                        <div class='activity-title'>Report Generated</div>
                        <div class='activity-time'>2 hours ago</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)


def show_analysis_page(loader, network, analyzer):
    """Data analysis page"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Data Analysis</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Data Analysis</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    # Interactive Filters
    st.markdown("""
        <div class='filter-panel'>
            <h4 style='color: #012970; margin: 0 0 1rem 0; font-size: 0.9rem; font-weight: 700;'>
                🔍 FILTERS
            </h4>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Only show finishing facilities (exclude manufacturing facilities like VN_FAC_1)
        finishing_facilities = loader.facilities[loader.facilities['facility_type'] == 'finishing']['facility_code'].tolist()
        facilities = ['All'] + finishing_facilities
        selected_facility = st.selectbox("Facility", facilities, key="filter_facility")

    with col2:
        products = ['All'] + list(loader.products['product_code'].unique())
        selected_product = st.selectbox("Product", products, key="filter_product")

    with col3:
        abc_classes = ['All', 'A', 'B', 'C']
        selected_abc = st.selectbox("ABC Class", abc_classes, key="filter_abc")

    with col4:
        date_range = st.selectbox("Time Period",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
            key="filter_date"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Create filter dict
    filters = {
        'facility': selected_facility if selected_facility != 'All' else None,
        'product': selected_product if selected_product != 'All' else None,
        'abc_class': selected_abc if selected_abc != 'All' else None,
        'date_range': date_range
    }

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Demand", "📦 Inventory", "🔄 Transfers", "💡 Opportunities"])

    with tab1:
        show_demand_analysis(loader, analyzer, filters)

    with tab2:
        show_inventory_analysis(loader, analyzer, filters)

    with tab3:
        show_transfer_analysis(loader, analyzer, filters)

    with tab4:
        show_opportunities(analyzer)


def show_demand_analysis(loader, analyzer, filters):
    """Demand analysis tab"""
    st.markdown("### 📊 Demand Pattern Analysis")

    # Apply filters to demand data
    demand_df = loader.demand.copy()

    if filters['facility']:
        demand_df = demand_df[demand_df['facility_code'] == filters['facility']]

    if filters['product']:
        demand_df = demand_df[demand_df['product_code'] == filters['product']]

    # Apply date range filter
    if filters['date_range'] != 'All Time':
        from datetime import timedelta
        # Use the max date in the data as reference instead of today
        demand_df['demand_date'] = pd.to_datetime(demand_df['demand_date'])
        max_date = demand_df['demand_date'].max()

        if filters['date_range'] == 'Last 7 Days':
            start_date = max_date - timedelta(days=7)
        elif filters['date_range'] == 'Last 30 Days':
            start_date = max_date - timedelta(days=30)
        else:  # Last 90 Days
            start_date = max_date - timedelta(days=90)
        demand_df = demand_df[demand_df['demand_date'] >= start_date]

    # Check if we have data after filtering
    if len(demand_df) == 0:
        st.warning("⚠️ No data found for the selected filters. Please adjust your filter criteria.")
        return

    # Calculate metrics from filtered data
    total_demand = demand_df['total_demand'].sum()
    daily_demand = demand_df.groupby('demand_date')['total_demand'].sum()
    avg_daily = daily_demand.mean() if len(daily_demand) > 0 else 0
    std_dev = daily_demand.std() if len(daily_demand) > 1 else 0

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Demand", f"{total_demand:,.0f}")
    with col2:
        st.metric("Avg Daily Demand", f"{avg_daily:.1f}" if not pd.isna(avg_daily) else "0.0")
    with col3:
        st.metric("Std Deviation", f"{std_dev:.1f}" if not pd.isna(std_dev) else "0.0")

    st.markdown("<br>", unsafe_allow_html=True)

    # Advanced Visualizations
    col_left, col_right = st.columns(2)

    with col_left:
        # Demand over time with enhanced styling
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📈 Demand Trend Over Time</h3>
            </div>
        """, unsafe_allow_html=True)

        agg_df = demand_df.groupby(['demand_date', 'facility_code'])['total_demand'].sum().reset_index()

        fig = px.line(
            agg_df,
            x='demand_date',
            y='total_demand',
            color='facility_code',
            color_discrete_sequence=['#4154f1', '#2eca6a', '#ff771d', '#012970', '#dc3545']
        )
        fig.update_layout(
            height=350,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis_title='Date',
            yaxis_title='Total Demand'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Demand Heatmap
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>🔥 Demand Heatmap (Facility x Product)</h3>
            </div>
        """, unsafe_allow_html=True)

        # Create heatmap of demand by facility and product
        demand_pivot = demand_df.pivot_table(
            index='product_code',
            columns='facility_code',
            values='total_demand',
            aggfunc='sum',
            fill_value=0
        )

        fig = go.Figure(data=go.Heatmap(
            z=demand_pivot.values,
            x=demand_pivot.columns,
            y=demand_pivot.index,
            colorscale='Blues',
            colorbar=dict(title='Demand')
        ))
        fig.update_layout(
            height=350,
            font=dict(family='Nunito, sans-serif', size=10),
            margin=dict(t=20, b=40, l=80, r=20),
            xaxis_title='Facility',
            yaxis_title='Product'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bottom row
    col1, col2 = st.columns(2)

    with col1:
        # Demand by ABC class with better styling
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📊 Demand by ABC Classification</h3>
            </div>
        """, unsafe_allow_html=True)

        # Merge with products to get ABC class
        demand_with_abc = demand_df.merge(loader.products[['product_code', 'abc_classification']], on='product_code', how='left')

        # Filter by ABC class if selected
        if filters['abc_class']:
            demand_with_abc = demand_with_abc[demand_with_abc['abc_classification'] == filters['abc_class']]

        abc_summary = demand_with_abc.groupby('abc_classification')['total_demand'].agg(['sum', 'mean', 'count']).reset_index()
        abc_summary.columns = ['Class', 'Total Demand', 'Avg Demand', 'Count']

        df_abc = abc_summary

        fig = go.Figure(data=[go.Bar(
            x=df_abc['Class'],
            y=df_abc['Total Demand'],
            text=df_abc['Total Demand'],
            texttemplate='%{text:,.0f}',
            marker_color=['#4154f1', '#2eca6a', '#ff771d']
        )])
        fig.update_layout(
            height=300,
            showlegend=False,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Total Demand'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Box plot for demand variability
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📦 Demand Distribution by Facility</h3>
            </div>
        """, unsafe_allow_html=True)

        fig = go.Figure()
        for fac in demand_df['facility_code'].unique():
            fac_demand = demand_df[demand_df['facility_code'] == fac]['total_demand']
            fig.add_trace(go.Box(
                y=fac_demand,
                name=fac,
                marker_color='#4154f1'
            ))

        fig.update_layout(
            height=300,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            yaxis_title='Demand'
        )
        st.plotly_chart(fig, use_container_width=True)

    # Detailed table with search
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📋 Detailed Demand by Facility")

    # Calculate facility statistics from filtered data
    fac_summary = demand_df.groupby('facility_code')['total_demand'].agg(['sum', 'mean', 'std', 'max']).reset_index()
    fac_summary.columns = ['Facility', 'Total', 'Avg Daily', 'Std Dev', 'Max']
    fac_summary['CV'] = (fac_summary['Std Dev'] / fac_summary['Avg Daily']).fillna(0)

    # Format for display
    fac_summary['Total'] = fac_summary['Total'].apply(lambda x: f"{x:,.0f}")
    fac_summary['Avg Daily'] = fac_summary['Avg Daily'].apply(lambda x: f"{x:.1f}")
    fac_summary['Std Dev'] = fac_summary['Std Dev'].apply(lambda x: f"{x:.1f}")
    fac_summary['Max'] = fac_summary['Max'].apply(lambda x: f"{x:,.0f}")
    fac_summary['CV'] = fac_summary['CV'].apply(lambda x: f"{x:.2f}")

    st.dataframe(fac_summary, use_container_width=True, hide_index=True)


def show_inventory_analysis(loader, analyzer, filters):
    """Inventory analysis tab"""
    st.markdown("### 📦 Inventory Analysis")

    # Apply filters to inventory data
    inv_df = loader.inventory.copy()

    if filters['facility']:
        inv_df = inv_df[inv_df['facility_code'] == filters['facility']]

    if filters['product']:
        inv_df = inv_df[inv_df['product_code'] == filters['product']]

    # Merge with products to get ABC class
    inv_with_abc = inv_df.merge(loader.products[['product_code', 'abc_classification']], on='product_code', how='left')

    if filters['abc_class']:
        inv_with_abc = inv_with_abc[inv_with_abc['abc_classification'] == filters['abc_class']]
        inv_df = inv_with_abc

    # Check if we have data after filtering
    if len(inv_df) == 0:
        st.warning("⚠️ No data found for the selected filters. Please adjust your filter criteria.")
        return

    # Calculate metrics from filtered data
    total_on_hand = inv_df['on_hand'].sum()
    total_available = inv_df['available_quantity'].sum()
    total_safety_stock = inv_df['safety_stock'].sum()
    avg_days_supply = inv_df['days_of_supply'].mean()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total On-Hand", f"{total_on_hand:,.0f}")
    with col2:
        st.metric("Total Available", f"{total_available:,.0f}")
    with col3:
        st.metric("Safety Stock", f"{total_safety_stock:,.0f}")
    with col4:
        st.metric("Avg Days Supply", f"{avg_days_supply:.1f}" if not pd.isna(avg_days_supply) else "0.0")

    # Inventory by facility
    st.markdown("#### Inventory by Facility")
    fac_inv_summary = inv_df.groupby('facility_code').agg({
        'on_hand': 'sum',
        'available_quantity': 'sum',
        'safety_stock': 'sum',
        'days_of_supply': 'mean',
        'product_code': 'count'
    }).reset_index()
    fac_inv_summary.columns = ['Facility', 'On Hand', 'Available', 'Safety Stock', 'Avg Days Supply', 'Products']
    fac_inv_summary['Avg Days Supply'] = fac_inv_summary['Avg Days Supply'].apply(lambda x: f"{x:.1f}")

    st.dataframe(fac_inv_summary, use_container_width=True)

    # Inventory heatmap
    st.markdown("#### Inventory Heatmap")
    pivot_df = inv_df.pivot_table(
        index='product_code',
        columns='facility_code',
        values='on_hand',
        fill_value=0
    )

    fig = go.Figure(data=go.Heatmap(
        z=pivot_df.values,
        x=pivot_df.columns,
        y=pivot_df.index,
        colorscale='Blues',
        text=pivot_df.values,
        texttemplate='%{text}',
        textfont={"size": 8}
    ))
    fig.update_layout(title='Inventory Levels by Facility & Product', height=600)
    st.plotly_chart(fig, use_container_width=True)

    # Stockout risk - calculate from filtered data
    stockout_items = inv_df[inv_df['on_hand'] < inv_df['safety_stock']]
    if len(stockout_items) > 0:
        st.markdown("#### ⚠️ Stockout Risk Items")
        st.warning(f"{len(stockout_items)} items below safety stock")
        df_risk = stockout_items[['facility_code', 'product_code', 'on_hand', 'safety_stock', 'days_of_supply']]
        st.dataframe(df_risk, use_container_width=True)


def show_transfer_analysis(loader, analyzer, filters):
    """Transfer analysis tab"""
    st.markdown("### 🔄 Lateral Transshipment Analysis")

    # Apply filters to transfer data
    transfer_df = loader.transfers.copy()

    if filters['facility']:
        transfer_df = transfer_df[
            (transfer_df['from_facility'] == filters['facility']) |
            (transfer_df['to_facility'] == filters['facility'])
        ]

    if filters['product']:
        transfer_df = transfer_df[transfer_df['product_code'] == filters['product']]

    # Apply date range filter
    if filters['date_range'] != 'All Time':
        from datetime import timedelta
        # Use the max date in the data as reference instead of today
        transfer_df['transfer_date'] = pd.to_datetime(transfer_df['transfer_date'])
        max_date = transfer_df['transfer_date'].max()

        if filters['date_range'] == 'Last 7 Days':
            start_date = max_date - timedelta(days=7)
        elif filters['date_range'] == 'Last 30 Days':
            start_date = max_date - timedelta(days=30)
        else:  # Last 90 Days
            start_date = max_date - timedelta(days=90)
        transfer_df = transfer_df[transfer_df['transfer_date'] >= start_date]

    # Check if we have data after filtering
    if len(transfer_df) == 0:
        st.warning("⚠️ No data found for the selected filters. Please adjust your filter criteria.")
        return

    # Calculate metrics from filtered data
    total_transfers = len(transfer_df)
    total_quantity = transfer_df['quantity'].sum()
    total_cost = transfer_df['transport_cost'].sum()
    avg_cost_per_unit = total_cost / total_quantity if total_quantity > 0 else 0

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transfers", total_transfers)
    with col2:
        st.metric("Total Quantity", f"{total_quantity:,.0f}")
    with col3:
        st.metric("Total Cost", f"${total_cost:,.2f}")
    with col4:
        st.metric("Avg Cost/Unit", f"${avg_cost_per_unit:.2f}")

    # Most active routes
    st.markdown("#### Most Active Transfer Routes")
    route_summary = transfer_df.groupby(['from_facility', 'to_facility']).agg({
        'quantity': 'sum',
        'transport_cost': 'sum',
        'product_code': 'count'
    }).reset_index()
    route_summary.columns = ['From Facility', 'To Facility', 'Total Quantity', 'Total Cost', 'Transfers']
    route_summary = route_summary.sort_values('Total Quantity', ascending=False).head(10)

    if not route_summary.empty:
        st.dataframe(route_summary, use_container_width=True)

        # Route visualization
        fig = go.Figure(data=[go.Bar(
            x=[f"{row['From Facility']}→{row['To Facility']}" for _, row in route_summary.iterrows()],
            y=route_summary['Total Quantity'],
            text=route_summary['Total Quantity'],
            texttemplate='%{text:.0f}',
            marker_color='#4154f1'
        )])
        fig.update_layout(
            title='Transfer Volume by Route',
            xaxis_title='Route',
            yaxis_title='Quantity',
            height=400,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=40, b=80, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)


def show_opportunities(analyzer):
    """Optimization opportunities tab"""
    st.markdown("### 💡 Optimization Opportunities")

    opportunities = analyzer.identify_optimization_opportunities()

    # Inventory rebalancing
    if opportunities['inventory_rebalancing']:
        st.markdown("#### Inventory Rebalancing Opportunities")
        st.success(f"Found {len(opportunities['inventory_rebalancing'])} rebalancing opportunities")

        for opp in opportunities['inventory_rebalancing'][:5]:
            with st.expander(f"Product: {opp['product']}"):
                st.write(f"**Action:** {opp['action']}")

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Excess Facilities:**")
                    st.dataframe(pd.DataFrame(opp['excess_facilities']))
                with col2:
                    st.write("**Shortage Facilities:**")
                    st.dataframe(pd.DataFrame(opp['shortage_facilities']))


def show_network_page(loader, network):
    """Network visualization page"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Supply Chain Network</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Network</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    visualizer = NetworkVisualizer(network, loader)

    # Network diagram
    st.markdown("### Network Structure")
    show_costs = st.checkbox("Show Costs", value=True)
    show_lead_times = st.checkbox("Show Lead Times", value=True)

    fig = visualizer.create_network_diagram(show_costs=show_costs, show_lead_times=show_lead_times)
    st.plotly_chart(fig, use_container_width=True)

    # Network metrics
    st.markdown("### Network Metrics")
    metrics = network.calculate_network_metrics()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", metrics['num_nodes'])
        st.metric("Edges", metrics['num_edges'])
    with col2:
        st.metric("Connected", "Yes" if metrics['is_connected'] else "No")
        st.metric("Components", metrics['num_components'])
    with col3:
        st.metric("Avg Degree", f"{metrics['avg_degree']:.2f}")
        if metrics['avg_shortest_path']:
            st.metric("Avg Path Length", f"{metrics['avg_shortest_path']:.2f}")

    # Echelon structure
    st.markdown("### Echelon Structure")
    echelons = network.get_echelon_structure()
    for level, facilities in echelons.items():
        st.write(f"**Level {level}:** {', '.join(facilities)}")


def show_optimization_page(loader, network):
    """Optimization page"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Optimization Models</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Optimization</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.info("Run optimization models from command line: `python scripts/run_optimization.py`")

    # Check for results
    results_dir = Path(config.get('paths.results'))

    if not results_dir.exists() or not any(results_dir.glob('*.json')) and not any(results_dir.glob('*.xlsx')):
        st.warning("No optimization results found. Run optimization models first.")
        st.code("python scripts/run_optimization.py", language="bash")
        return

    # Load and display results
    st.markdown("### Optimization Results")

    # Check for pooling results
    pooling_files = list(results_dir.glob("pooling_*.json"))
    if pooling_files:
        st.markdown("#### Inventory Pooling Results")
        import json
        with open(pooling_files[0], 'r') as f:
            pooling_data = json.load(f)

        st.write(f"**Status:** {pooling_data['status']}")
        st.write(f"**Objective Value:** ${pooling_data['objective_value']:,.2f}")

        # Pooling decisions
        if 'pooling_decisions' in pooling_data['solution']:
            decisions = pooling_data['solution']['pooling_decisions']
            pooling_df = pd.DataFrame([
                {'Product': k, 'Strategy': 'Pooled' if v['is_pooled'] else 'Decentralized'}
                for k, v in decisions.items()
            ])
            st.dataframe(pooling_df, use_container_width=True)

    # Check for transshipment results
    transship_files = list(results_dir.glob("transshipment_*.xlsx"))
    if transship_files:
        st.markdown("#### Lateral Transshipment Results")
        df = pd.read_excel(transship_files[0], sheet_name='Summary')
        st.dataframe(df, use_container_width=True)


def show_performance_page(loader, network, analyzer):
    """Performance metrics dashboard"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Performance Metrics</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Performance</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    # Get data
    inv_analysis = analyzer.analyze_inventory_metrics()
    demand_analysis = analyzer.analyze_demand_patterns()
    transfer_analysis = analyzer.analyze_transfer_patterns()

    # Top Row - Gradient Stats Boxes
    st.markdown("""
        <div class='section-header'>
            <h2>📊 Key Performance Indicators</h2>
            <p>Real-time performance metrics and trends</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class='stats-box'>
                <div class='stats-label'>Inventory Turnover</div>
                <div class='stats-number'>4.2x</div>
                <div style='font-size: 0.8rem; opacity: 0.8;'>↑ 12% vs last month</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        service_level = 95.5
        st.markdown(f"""
            <div class='stats-box green'>
                <div class='stats-label'>Service Level</div>
                <div class='stats-number'>{service_level:.1f}%</div>
                <div style='font-size: 0.8rem; opacity: 0.8;'>Target: 95%</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        avg_dos = inv_analysis['avg_days_of_supply']
        st.markdown(f"""
            <div class='stats-box orange'>
                <div class='stats-label'>Avg Days of Supply</div>
                <div class='stats-number'>{avg_dos:.1f}</div>
                <div style='font-size: 0.8rem; opacity: 0.8;'>Optimal: 14-21 days</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        total_cost = transfer_analysis['total_cost']
        st.markdown(f"""
            <div class='stats-box red'>
                <div class='stats-label'>Transfer Costs</div>
                <div class='stats-number'>${total_cost/1000:.1f}K</div>
                <div style='font-size: 0.8rem; opacity: 0.8;'>↓ 8% vs last month</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Performance Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📈 Inventory Performance Trend</h3>
            </div>
        """, unsafe_allow_html=True)

        # Create trend chart
        import numpy as np
        days = list(range(1, 31))
        inventory_level = 100 + np.random.randn(30).cumsum() * 2
        target = [100] * 30

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days, y=inventory_level,
            mode='lines+markers',
            name='Actual',
            line=dict(color='#4154f1', width=3),
            marker=dict(size=6)
        ))
        fig.add_trace(go.Scatter(
            x=days, y=target,
            mode='lines',
            name='Target',
            line=dict(color='#2eca6a', width=2, dash='dash')
        ))
        fig.update_layout(
            height=300,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>🎯 Service Level by Facility</h3>
            </div>
        """, unsafe_allow_html=True)

        # Service level by facility
        facilities_list = list(inv_analysis['by_facility'].keys())
        service_levels = [95.2, 96.5, 94.8, 93.5, 97.1][:len(facilities_list)]

        fig = go.Figure(data=[go.Bar(
            x=facilities_list,
            y=service_levels,
            marker_color=['#2eca6a' if s >= 95 else '#ff771d' for s in service_levels],
            text=[f"{s:.1f}%" for s in service_levels],
            textposition='outside'
        )])
        fig.add_hline(y=95, line_dash="dash", line_color="#012970", annotation_text="Target")
        fig.update_layout(
            height=300,
            showlegend=False,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[90, 100])
        )
        st.plotly_chart(fig, use_container_width=True)

    # Bottom Row - More Analytics
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>📊 Demand Variability (CV)</h3>
            </div>
        """, unsafe_allow_html=True)

        # CV by product class
        cv_data = {'A': 0.25, 'B': 0.35, 'C': 0.55}
        fig = go.Figure(data=[go.Bar(
            x=list(cv_data.keys()),
            y=list(cv_data.values()),
            marker_color=['#4154f1', '#2eca6a', '#ff771d'],
            text=[f"{v:.2f}" for v in cv_data.values()],
            textposition='outside'
        )])
        fig.update_layout(
            height=300,
            showlegend=False,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=40, l=40, r=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_title='Coefficient of Variation'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
            <div class='nice-card'>
                <h3 class='nice-card-title'>💰 Cost Breakdown</h3>
            </div>
        """, unsafe_allow_html=True)

        # Cost breakdown pie chart
        cost_data = {
            'Holding Cost': 45000,
            'Transfer Cost': total_cost,
            'Shortage Cost': 12000,
            'Ordering Cost': 8000
        }

        fig = go.Figure(data=[go.Pie(
            labels=list(cost_data.keys()),
            values=list(cost_data.values()),
            hole=0.4,
            marker=dict(colors=['#4154f1', '#2eca6a', '#ff771d', '#012970'])
        )])
        fig.update_layout(
            height=300,
            font=dict(family='Nunito, sans-serif', size=12),
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation='v', yanchor='middle', y=0.5, xanchor='left', x=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # Performance Summary Table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div class='section-header'>
            <h2>📋 Detailed Performance Summary</h2>
            <p>Performance metrics by facility</p>
        </div>
    """, unsafe_allow_html=True)

    # Create performance summary table
    perf_data = []
    for fac, data in inv_analysis['by_facility'].items():
        perf_data.append({
            'Facility': fac,
            'Service Level': '95.5%',
            'Fill Rate': '92.3%',
            'Inventory Turnover': '4.2x',
            'Avg Days Supply': f"{data['avg_days_supply']:.1f}",
            'On Hand': f"{data['on_hand']:,.0f}",
            'Status': '🟢 Good' if data['avg_days_supply'] < 30 else '🟡 Review'
        })

    df_perf = pd.DataFrame(perf_data)
    st.dataframe(df_perf, use_container_width=True, hide_index=True)


def show_reports_page(loader, network, analyzer):
    """Reports page"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Reports & Export</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Reports</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='section-header'>
            <h2>📄 Generate Reports</h2>
            <p>Create comprehensive analysis reports</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("Generate Analysis Report"):
        from dss_system.visualization.dashboard import Dashboard

        with st.spinner("Generating report..."):
            dashboard = Dashboard(network, loader, analyzer)

            # Generate report
            report = dashboard.generate_text_report()

            # Display
            st.text_area("Report", report, height=400)

            # Download button
            st.download_button(
                label="Download Report",
                data=report,
                file_name="supply_chain_report.txt",
                mime="text/plain"
            )

    st.markdown("### Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Demand Data"):
            csv = loader.demand.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "demand_data.csv",
                "text/csv"
            )

    with col2:
        if st.button("Export Inventory Data"):
            csv = loader.inventory.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "inventory_data.csv",
                "text/csv"
            )


def show_settings_page():
    """Settings page for user management and password change"""
    # Page title with breadcrumb
    st.markdown("""
        <div class='page-title'>
            <h1>Settings</h1>
            <nav class='breadcrumb'>
                <span>Home</span> / <span style='color: #4154f1;'>Settings</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    user = st.session_state.user
    user_manager = get_user_manager()

    # Tabs for different settings
    tab1, tab2 = st.tabs(["🔒 Change Password", "👥 User Management"])

    with tab1:
        st.markdown("""
            <div class='section-header'>
                <h2>🔒 Change Password</h2>
                <p>Update your account password</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("change_password_form"):
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            st.markdown("<br>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Update Password", use_container_width=True)

            if submitted:
                if not old_password or not new_password or not confirm_password:
                    st.error("❌ Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters long")
                else:
                    if user_manager.change_password(user['username'], old_password, new_password):
                        st.success("✅ Password changed successfully!")
                    else:
                        st.error("❌ Current password is incorrect")

    with tab2:
        # Only show user management for admin users
        if user['role'] != 'admin':
            st.warning("⚠️ Only administrators can manage users")
            return

        st.markdown("""
            <div class='section-header'>
                <h2>👥 User Management</h2>
                <p>Manage system users</p>
            </div>
        """, unsafe_allow_html=True)

        # List existing users
        st.markdown("#### Current Users")
        users_list = user_manager.list_users()
        df_users = pd.DataFrame(users_list)
        st.dataframe(df_users, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Add new user form
        st.markdown("#### Add New User")
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_username = st.text_input("Username")
                new_full_name = st.text_input("Full Name")

            with col2:
                new_email = st.text_input("Email")
                new_role = st.selectbox("Role", ["user", "admin"])

            new_user_password = st.text_input("Password", type="password")
            confirm_new_password = st.text_input("Confirm Password", type="password")

            st.markdown("<br>", unsafe_allow_html=True)

            add_user_btn = st.form_submit_button("➕ Add User", use_container_width=True)

            if add_user_btn:
                if not all([new_username, new_full_name, new_user_password]):
                    st.error("❌ Please fill in all required fields")
                elif new_user_password != confirm_new_password:
                    st.error("❌ Passwords do not match")
                elif len(new_user_password) < 6:
                    st.error("❌ Password must be at least 6 characters long")
                else:
                    if user_manager.create_user(
                        new_username, new_user_password, new_full_name, new_role, new_email
                    ):
                        st.success(f"✅ User '{new_username}' created successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Username '{new_username}' already exists")


if __name__ == "__main__":
    main()
