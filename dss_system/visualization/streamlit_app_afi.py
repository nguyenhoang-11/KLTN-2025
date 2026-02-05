"""
AFI Supply Chain Dashboard - Enterprise Version
Real-world data from Ashley Furniture Industries

Dashboard for analyzing:
- 4,820 items across 17 warehouses
- 12-week forecast analysis
- Inventory position (balance vs bounds)
- Transshipment opportunities
- Performance metrics

Run with: streamlit run dss_system/visualization/streamlit_app_afi.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dss_system.data.loader_afi import AFIDataLoader
from dss_system.optimization import DestinationChangeOptimizer
from dss_system.utils.summary_generator import SummaryGenerator, render_summary_streamlit

# Page configuration
st.set_page_config(
    page_title="AFI Supply Chain DSS",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - NiceAdmin inspired
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap');

    * { font-family: 'Nunito', sans-serif; }

    .main { padding: 1rem 2rem; background-color: #f6f9ff; }

    h1 { color: #012970; font-weight: 700; font-size: 2rem; margin-bottom: 1rem; }
    h2 { color: #012970; font-weight: 600; font-size: 1.5rem; margin-top: 1.5rem; }
    h3 { color: #012970; font-weight: 600; font-size: 1.25rem; margin-bottom: 1rem; }

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
    }

    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #012970 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] {
        background: #fff;
        border-right: 1px solid #e3e6ef;
    }

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
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #4154f1 !important;
        border-bottom: 2px solid #4154f1;
    }

    .alert-success {
        background-color: #d1e7dd;
        border-left: 4px solid #198754;
        padding: 1rem;
        border-radius: 4px;
        color: #0f5132;
        margin: 1rem 0;
    }

    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 4px;
        color: #997404;
        margin: 1rem 0;
    }

    .alert-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 4px;
        color: #842029;
        margin: 1rem 0;
    }

    .kpi-positive { color: #2eca6a; font-weight: 700; }
    .kpi-negative { color: #dc3545; font-weight: 700; }
    .kpi-warning { color: #ff771d; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def load_afi_data():
    """Load AFI data with caching"""
    loader = AFIDataLoader()
    loader.load_all()
    return loader


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_summary_stats(_loader, week):
    """Cache summary stats to improve performance"""
    return _loader.get_summary_stats(week)


@st.cache_data(ttl=300)
def get_cached_shortages(_loader, week):
    """Cache shortage data"""
    return _loader.get_shortages(week)


@st.cache_data(ttl=300)
def get_cached_excess(_loader, week):
    """Cache excess data"""
    return _loader.get_excess(week)


@st.cache_data(ttl=300)
def get_cached_transshipment_opportunities(_loader, week):
    """Cache transshipment opportunities (expensive computation)"""
    return _loader.identify_transshipment_opportunities(week)


@st.cache_data(ttl=300)
def get_cached_inventory_position(_loader, week):
    """Cache inventory position data"""
    return _loader.get_inventory_position(week)


def main():
    # Sidebar
    st.sidebar.markdown("""
        <div style='text-align: center; padding: 2rem 0 1.5rem 0; border-bottom: 1px solid #ebeef4;'>
            <div style='font-size: 2.5rem; margin-bottom: 0.5rem;'></div>
            <h2 style='color: #012970; margin: 0; font-size: 1.25rem; font-weight: 700;'>AFI Supply Chain</h2>
            <p style='color: #899bbd; font-size: 0.75rem; margin-top: 0.25rem; font-weight: 600;'>
                ENTERPRISE DSS
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    page = st.sidebar.radio(
        "NAVIGATION",
        [" Overview", " Forecast Analysis", " Inventory Position",
         " Transshipment", " Performance", " Reports", " Optimization"],
        label_visibility="visible"
    )

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # Data info
    st.sidebar.markdown("""
        <div style='background: #fff; border-radius: 5px; padding: 1rem; margin: 1rem 0;
                    box-shadow: 0px 0 20px rgba(1, 41, 112, 0.1); border-left: 3px solid #4154f1;'>
            <h4 style='color: #012970; margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 700;'>
                INFO: DATA SOURCE
            </h4>
            <p style='color: #899bbd; font-size: 0.8rem; margin: 0; line-height: 1.6;'>
                <strong style='color: #012970;'>Ashley Furniture Industries</strong><br>
                Real enterprise supply chain data<br>
                4,820 items x 17 warehouses<br>
                12-week forecast horizon
            </p>
        </div>
    """, unsafe_allow_html=True)

    # System status
    st.sidebar.markdown("""
        <div style='background: #d1e7dd; border-left: 3px solid #198754;
                    border-radius: 5px; padding: 0.875rem; margin: 1rem 0;'>
            <p style='color: #0f5132; margin: 0; font-size: 0.8rem; line-height: 1.8;'>
                <span style='display: inline-block; width: 8px; height: 8px; background: #198754;
                             border-radius: 50%; margin-right: 0.5rem;'></span>
                <strong>Status:</strong> Online<br>
                <span style='margin-left: 1.25rem;'>📅 Data: Real-time</span><br>
                <span style='margin-left: 1.25rem;'>⚡ Performance: Optimal</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("<br>", unsafe_allow_html=True)

    # AI Summary Configuration
    with st.sidebar.expander("AI Summary Settings", expanded=False):
        st.markdown("""
        <p style='font-size: 0.8rem; color: #666;'>
        Enter your Google Gemini API key to enable AI-powered summaries.
        Get a free key at <a href='https://makersuite.google.com/app/apikey' target='_blank'>Google AI Studio</a>.
        </p>
        """, unsafe_allow_html=True)

        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.get('gemini_api_key', ''),
            help="Leave empty to use template-based summaries"
        )

        if api_key_input:
            st.session_state['gemini_api_key'] = api_key_input
            st.success("API key saved for this session", icon="check")
        elif 'gemini_api_key' in st.session_state:
            del st.session_state['gemini_api_key']

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style='text-align: center; color: #899bbd; font-size: 0.7rem; padding-top: 1rem;
                    border-top: 1px solid #ebeef4;'>
            <p style='margin: 0.25rem 0;'>Powered by Streamlit & Python</p>
            <p style='margin: 0.25rem 0;'>© 2025 KLTN Project</p>
        </div>
    """, unsafe_allow_html=True)

    # Load data
    with st.spinner(" Loading AFI enterprise data... Please wait."):
        loader = load_afi_data()

    # Route to pages
    if page == " Overview":
        show_overview_page(loader)
    elif page == " Forecast Analysis":
        show_forecast_page(loader)
    elif page == " Inventory Position":
        show_inventory_page(loader)
    elif page == " Transshipment":
        show_transshipment_page(loader)
    elif page == " Performance":
        show_performance_page(loader)
    elif page == " Reports":
        show_reports_page(loader)
    elif page == " Optimization":
        show_optimization_page(loader)


# =============================================================================
# PAGE 1: OVERVIEW
# =============================================================================

def show_overview_page(loader):
    """Overview page with KPIs"""
    st.markdown("""
        <div class='page-title'>
            <h1>Dashboard Overview</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Dashboard</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='margin-bottom: 1.5rem;'>
            <h2 style='margin: 0;'> Key Performance Indicators</h2>
            <p style='color: #899bbd; font-size: 0.875rem; margin-top: 0.25rem;'>
                Real-time metrics for supply chain performance monitoring
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Get summary stats (cached for performance)
    summary = get_cached_summary_stats(loader, week='W3')

    # Top KPIs
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Warehouses",
            summary['total_warehouses'],
            help="Number of warehouses in network"
        )
        st.metric(
            "Total Items",
            f"{summary['total_items']:,}",
            help="Unique product codes"
        )

    with col2:
        st.metric(
            "Total SKUs",
            f"{summary['total_skus']:,}",
            help="Item x Warehouse combinations"
        )
        st.metric(
            "Coverage %",
            f"{summary['coverage_percentage']:.1f}%",
            delta=f"{summary['coverage_percentage'] - 95:.1f}%",
            help="% of items meeting safety stock"
        )

    with col3:
        st.metric(
            "Items at Risk",
            summary['items_below_lower'],
            delta=f"-{summary['items_below_lower']}" if summary['items_below_lower'] > 0 else "0",
            delta_color="inverse",
            help="Items below safety stock (shortage)"
        )
        st.metric(
            "Excess Items",
            summary['items_above_upper'],
            delta=f"-{summary['items_above_upper']}" if summary['items_above_upper'] > 0 else "0",
            delta_color="inverse",
            help="Items above maximum stock"
        )

    with col4:
        st.metric(
            "Backorder Risk",
            f"${summary['total_backorder_risk']:,.0f}",
            help="Total potential backorder cost"
        )
        st.metric(
            "Hot List Items",
            summary['hot_list_items'],
            help="Priority items requiring attention"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
            <div class='nice-card'>
                <h3 style='color: #012970; margin-bottom: 1rem;'> Inventory Health Status</h3>
            </div>
        """, unsafe_allow_html=True)

        # Get position data (cached)
        position = get_cached_inventory_position(loader, 'W3')

        if not position.empty:
            # Categorize
            below = len(position[position['BALANCE'] < position['LOWER_BOUND']])
            ok = len(position[(position['BALANCE'] >= position['LOWER_BOUND']) &
                             (position['BALANCE'] <= position['UPPER_BOUND'])])
            above = len(position[position['BALANCE'] > position['UPPER_BOUND']])

            fig = go.Figure(data=[go.Bar(
                x=['Below Lower', 'Healthy', 'Above Upper'],
                y=[below, ok, above],
                marker_color=['#dc3545', '#2eca6a', '#ff771d'],
                text=[below, ok, above],
                texttemplate='%{text:,}',
                textposition='outside'
            )])
            fig.update_layout(
                height=300,
                showlegend=False,
                font=dict(family='Nunito, sans-serif', size=12),
                margin=dict(t=20, b=40, l=40, r=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_title='Number of SKUs'
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
            <div class='nice-card'>
                <h3 style='color: #012970; margin-bottom: 1rem;'> Backorder Risk by Warehouse</h3>
            </div>
        """, unsafe_allow_html=True)

        shortages = get_cached_shortages(loader, 'W3')

        if not shortages.empty and 'BACKORDER_RISK_COST' in shortages.columns:
            # Group by warehouse
            risk_by_wh = shortages.groupby('WAREHOUSE')['BACKORDER_RISK_COST'].sum().sort_values(ascending=False).head(10)

            fig = go.Figure(data=[go.Bar(
                x=risk_by_wh.index.astype(str),
                y=risk_by_wh.values,
                marker_color='#dc3545',
                text=['$' + f"{v:,.0f}" for v in risk_by_wh.values],
                textposition='outside'
            )])
            fig.update_layout(
                height=300,
                showlegend=False,
                font=dict(family='Nunito, sans-serif', size=12),
                margin=dict(t=20, b=40, l=40, r=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Warehouse',
                yaxis_title='Backorder Risk ($)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No backorder risk data available")

    # Alerts section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## WARNING: Alerts & Recommendations")

    col1, col2 = st.columns([2, 1])

    with col1:
        if summary['items_below_lower'] > 0:
            st.markdown(f"""
                <div class='alert-danger'>
                    <strong>WARNING: CRITICAL:</strong> {summary['items_below_lower']:,} items below safety stock<br>
                    Recommended action: Initiate transshipment or emergency orders
                </div>
            """, unsafe_allow_html=True)

        if summary['items_above_upper'] > 0:
            st.markdown(f"""
                <div class='alert-warning'>
                    <strong>INFO: WARNING:</strong> {summary['items_above_upper']:,} items above maximum stock<br>
                    Recommended action: Review for potential redistribution
                </div>
            """, unsafe_allow_html=True)

        if summary['transshipment_opportunities'] > 0:
            st.markdown(f"""
                <div class='alert-success'>
                    <strong> OPPORTUNITY:</strong> {summary['transshipment_opportunities']} transshipment opportunities identified<br>
                    Potential savings: <span class='kpi-positive'>${summary['total_potential_savings']:,.0f}</span>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🔥 Hot List Summary")
        hot_list = loader.get_hot_list_items()
        if not hot_list.empty:
            st.metric("Priority Items", len(hot_list))
            if 'REASON' in hot_list.columns:
                top_reasons = hot_list['REASON'].value_counts().head(3)
                for reason, count in top_reasons.items():
                    st.write(f"• {reason}: **{count}** items")
        else:
            st.info("No hot list items")


# =============================================================================
# PAGE 2: FORECAST ANALYSIS
# =============================================================================

def show_forecast_page(loader):
    """Forecast analysis page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Forecast Analysis</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Forecast Analysis</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("###  12-Week Safety Stock Forecast")

    # Get forecast data
    forecast = loader.get_forecast_data()

    if forecast.empty:
        st.warning("No forecast data available")
        return

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        # Convert all to string before sorting
        warehouses = ['All'] + sorted([str(w) for w in forecast['WHSE'].unique().tolist()])
        selected_wh = st.selectbox("Warehouse", warehouses)

    with col2:
        # Convert all to string before sorting
        items = ['All'] + sorted([str(i) for i in forecast['ITEM'].unique().tolist()])[:100]  # Limit for performance
        selected_item = st.selectbox("Item (top 100)", items)

    # Filter data
    filtered = forecast.copy()
    if selected_wh != 'All':
        # Convert WHSE to string for comparison
        filtered = filtered[filtered['WHSE'].astype(str) == selected_wh]
    if selected_item != 'All':
        # Convert ITEM to string for comparison
        filtered = filtered[filtered['ITEM'].astype(str) == selected_item]

    if filtered.empty:
        st.warning("No data for selected filters")
        return

    # Forecast trend chart
    st.markdown("#### Safety Stock Trend by Week")

    if selected_item != 'All':
        # Single item - show by warehouse
        fig = px.line(
            filtered,
            x='WEEK_NUMBER',
            y='SAFETY_STOCK',
            color='WHSE',
            markers=True,
            title=f"Safety Stock Forecast: {selected_item}"
        )
    else:
        # Aggregate
        agg = filtered.groupby(['WEEK_NUMBER', 'WEEK'])['SAFETY_STOCK'].sum().reset_index()
        fig = px.line(
            agg,
            x='WEEK_NUMBER',
            y='SAFETY_STOCK',
            markers=True,
            title="Total Safety Stock Forecast (All Items)"
        )

    fig.update_layout(
        height=400,
        font=dict(family='Nunito, sans-serif', size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Week Number',
        yaxis_title='Safety Stock (units)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.markdown("#### Forecast Summary by Week")

    summary_table = filtered.groupby('WEEK_NUMBER').agg({
        'SAFETY_STOCK': ['sum', 'mean', 'std'],
        'ITEM': 'count'
    }).reset_index()
    summary_table.columns = ['Week', 'Total SS', 'Avg SS', 'Std Dev', 'Items']
    summary_table['Total SS'] = summary_table['Total SS'].apply(lambda x: f"{x:,.0f}")
    summary_table['Avg SS'] = summary_table['Avg SS'].apply(lambda x: f"{x:.1f}")
    summary_table['Std Dev'] = summary_table['Std Dev'].apply(lambda x: f"{x:.1f}")

    st.dataframe(summary_table, use_container_width=True, hide_index=True)


# =============================================================================
# PAGE 3: INVENTORY POSITION
# =============================================================================

def show_inventory_page(loader):
    """Inventory position analysis page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Inventory Position</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Inventory Position</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    # Week selector
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        week = st.selectbox("Select Week", ['W3', 'W4', 'W5', 'W6'])

    # Get data (cached for performance)
    position = get_cached_inventory_position(loader, week)
    shortages = get_cached_shortages(loader, week)
    excess = get_cached_excess(loader, week)

    if position.empty:
        st.warning("No inventory position data available")
        return

    # Summary metrics
    st.markdown("###  Inventory Status Summary")

    col1, col2, col3, col4 = st.columns(4)

    total_items = len(position)
    healthy = total_items - len(shortages) - len(excess)

    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Total SKUs</h4>
                <div class='kpi-value'>{total_items:,}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        pct = (len(shortages) / total_items * 100) if total_items > 0 else 0
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Below Lower Bound</h4>
                <div class='kpi-value kpi-negative'>{len(shortages):,}</div>
                <small style='color: #dc3545;'>{pct:.1f}%</small>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        pct = (healthy / total_items * 100) if total_items > 0 else 0
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Healthy Inventory</h4>
                <div class='kpi-value kpi-positive'>{healthy:,}</div>
                <small style='color: #198754;'>{pct:.1f}%</small>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        pct = (len(excess) / total_items * 100) if total_items > 0 else 0
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Above Upper Bound</h4>
                <div class='kpi-value kpi-warning'>{len(excess):,}</div>
                <small style='color: #ffc107;'>{pct:.1f}%</small>
            </div>
        """, unsafe_allow_html=True)

    # Inventory heatmap
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Inventory Level Heatmap")

    # Create status column
    position['STATUS'] = 'HEALTHY'
    position.loc[position['BALANCE'] < position['LOWER_BOUND'], 'STATUS'] = 'SHORTAGE'
    position.loc[position['BALANCE'] > position['UPPER_BOUND'], 'STATUS'] = 'EXCESS'

    # Pivot for heatmap
    heatmap_data = position.pivot_table(
        index='ITEM',
        columns='WAREHOUSE',
        values='BALANCE',
        aggfunc='sum'
    )

    # Limit to top 50 items for visibility
    if len(heatmap_data) > 50:
        heatmap_data = heatmap_data.head(50)
        st.info("Showing top 50 items. Use filters below for detailed analysis.")

    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Warehouse", y="Item", color="Balance"),
        color_continuous_scale='RdYlGn',
        aspect="auto"
    )
    fig.update_layout(
        height=500,
        font=dict(family='Nunito, sans-serif', size=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Shortage details
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Shortage Items (Below Lower Bound)")

    if not shortages.empty:
        # Display table
        shortage_display = shortages[[
            'ITEM', 'WAREHOUSE', 'BALANCE', 'LOWER_BOUND', 'SHORTAGE_QTY'
        ]].copy()

        if 'BACKORDER_RISK_COST' in shortages.columns:
            shortage_display['BACKORDER_RISK_COST'] = shortages['BACKORDER_RISK_COST']
            shortage_display = shortage_display.sort_values('BACKORDER_RISK_COST', ascending=False)

        # Format numbers
        shortage_display['BALANCE'] = shortage_display['BALANCE'].apply(lambda x: f"{x:,.0f}")
        shortage_display['LOWER_BOUND'] = shortage_display['LOWER_BOUND'].apply(lambda x: f"{x:,.0f}")
        shortage_display['SHORTAGE_QTY'] = shortage_display['SHORTAGE_QTY'].apply(lambda x: f"{x:,.0f}")
        if 'BACKORDER_RISK_COST' in shortage_display.columns:
            shortage_display['BACKORDER_RISK_COST'] = shortage_display['BACKORDER_RISK_COST'].apply(lambda x: f"${x:,.2f}")

        st.dataframe(shortage_display.head(50), use_container_width=True, hide_index=True)

        # Total risk
        if 'BACKORDER_RISK_COST' in shortages.columns:
            total_risk = shortages['BACKORDER_RISK_COST'].sum()
            st.markdown(f"""
                <div class='alert-danger'>
                    <strong>Total Backorder Risk:</strong> <span style='font-size: 1.5rem; font-weight: bold;'>${total_risk:,.0f}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No shortage items - all inventory levels are adequate!")

    # Excess details
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Excess Items (Above Upper Bound)")

    if not excess.empty:
        excess_display = excess[[
            'ITEM', 'WAREHOUSE', 'BALANCE', 'UPPER_BOUND', 'EXCESS_QTY'
        ]].copy()

        # Format numbers
        excess_display['BALANCE'] = excess_display['BALANCE'].apply(lambda x: f"{x:,.0f}")
        excess_display['UPPER_BOUND'] = excess_display['UPPER_BOUND'].apply(lambda x: f"{x:,.0f}")
        excess_display['EXCESS_QTY'] = excess_display['EXCESS_QTY'].apply(lambda x: f"{x:,.0f}")

        st.dataframe(excess_display.head(50), use_container_width=True, hide_index=True)

        total_excess = excess['EXCESS_QTY'].sum()
        st.info(f"Total excess inventory: **{total_excess:,.0f}** units across {len(excess)} SKUs")
    else:
        st.success("No excess inventory - all levels are within bounds!")


# =============================================================================
# PAGE 4: TRANSSHIPMENT OPPORTUNITIES
# =============================================================================

def show_transshipment_page(loader):
    """Transshipment opportunities page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Transshipment Opportunities</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Transshipment</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='background: #f6f9ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #4154f1; margin-bottom: 1.5rem;'>
            <strong>INFO: About Transshipment:</strong> Lateral transshipment involves moving inventory between
            facilities at the same echelon to balance shortages and excess. This analysis matches items with
            shortages to warehouses with excess inventory of the same item.
        </div>
    """, unsafe_allow_html=True)

    # Week selector
    col1, col2 = st.columns([1, 3])
    with col1:
        week = st.selectbox("Select Week", ['W3', 'W4', 'W5', 'W6'], key='trans_week')

    # Get opportunities (cached - this is the most expensive operation)
    opportunities = get_cached_transshipment_opportunities(loader, week)

    if not opportunities:
        st.warning("No transshipment opportunities identified for this week")
        return

    # Summary metrics
    st.markdown("###  Opportunity Summary")

    col1, col2, col3, col4 = st.columns(4)

    total_opportunities = len(opportunities)
    high_priority = len([o for o in opportunities if o['priority'] == 'HIGH'])
    total_savings = sum(o['net_benefit'] for o in opportunities)
    total_units = sum(o['transfer_qty'] for o in opportunities)

    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Total Opportunities</h4>
                <div class='kpi-value'>{total_opportunities}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>High Priority</h4>
                <div class='kpi-value kpi-negative'>{high_priority}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Potential Savings</h4>
                <div class='kpi-value kpi-positive'>${total_savings:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Total Units to Transfer</h4>
                <div class='kpi-value'>{total_units:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)

    # Opportunity table
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Recommended Transfers")

    # Convert to DataFrame for display
    opp_df = pd.DataFrame(opportunities)

    # Priority filter
    priority_filter = st.multiselect(
        "Filter by Priority",
        ['HIGH', 'MEDIUM'],
        default=['HIGH', 'MEDIUM']
    )

    filtered_opp = opp_df[opp_df['priority'].isin(priority_filter)]

    if filtered_opp.empty:
        st.info("No opportunities match the selected filters")
    else:
        # Display table
        display_cols = [
            'priority', 'item', 'from_warehouse', 'to_warehouse',
            'transfer_qty', 'shortage_qty', 'excess_qty',
            'avoided_backorder_cost', 'transport_cost', 'net_benefit'
        ]

        display_df = filtered_opp[display_cols].copy()
        display_df.columns = [
            'Priority', 'Item', 'From WH', 'To WH',
            'Transfer Qty', 'Shortage Qty', 'Excess Qty',
            'Avoided Cost', 'Transport Cost', 'Net Benefit'
        ]

        # Format numbers
        for col in ['Transfer Qty', 'Shortage Qty', 'Excess Qty']:
            display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")

        for col in ['Avoided Cost', 'Transport Cost', 'Net Benefit']:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

        # Color code priority
        def highlight_priority(row):
            if row['Priority'] == 'HIGH':
                return ['background-color: #fff3cd'] * len(row)
            return [''] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_priority, axis=1),
            use_container_width=True,
            hide_index=True
        )

    # Network flow visualization
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Transfer Flow Network")

    if len(filtered_opp) > 0:
        # Create Sankey diagram
        sources = []
        targets = []
        values = []
        labels = set()

        for _, row in filtered_opp.iterrows():
            from_wh = row['from_warehouse']
            to_wh = row['to_warehouse']
            qty = row['transfer_qty']

            labels.add(from_wh)
            labels.add(to_wh)

            sources.append(from_wh)
            targets.append(to_wh)
            values.append(qty)

        # Map to indices
        label_list = sorted(list(labels))
        label_to_idx = {label: idx for idx, label in enumerate(label_list)}

        source_indices = [label_to_idx[s] for s in sources]
        target_indices = [label_to_idx[t] for t in targets]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=label_list,
                color="#4154f1"
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color="rgba(65, 84, 241, 0.3)"
            )
        )])

        fig.update_layout(
            title="Transshipment Flow (From → To Warehouses)",
            font=dict(family='Nunito, sans-serif', size=12),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    # Action recommendations
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Action Recommendations")

    high_priority_opps = [o for o in opportunities if o['priority'] == 'HIGH']

    if high_priority_opps:
        st.markdown(f"""
            <div class='alert-danger'>
                <strong>WARNING: IMMEDIATE ACTION REQUIRED:</strong><br>
                {len(high_priority_opps)} high-priority transfers identified with total potential savings of
                <strong>${sum(o['net_benefit'] for o in high_priority_opps):,.0f}</strong>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("**Top 5 High-Priority Transfers:**")
        for i, opp in enumerate(high_priority_opps[:5], 1):
            st.markdown(f"""
                {i}. **{opp['item']}**: Transfer {opp['transfer_qty']:.0f} units from
                **{opp['from_warehouse']}** → **{opp['to_warehouse']}**
                (Net benefit: **${opp['net_benefit']:,.2f}**)
            """)
    else:
        st.success("No high-priority transfers at this time. Monitor medium-priority opportunities.")


# =============================================================================
# PAGE 5: PERFORMANCE METRICS
# =============================================================================

def show_performance_page(loader):
    """Performance metrics and trends page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Performance Metrics</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Performance</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    # Get data for all weeks
    weeks = ['W3', 'W4', 'W5', 'W6']

    # Collect metrics across weeks
    coverage_trend = []
    backorder_trend = []
    shortage_trend = []
    excess_trend = []

    for week in weeks:
        summary = get_cached_summary_stats(loader, week)
        coverage_trend.append({
            'Week': week,
            'Coverage %': summary['coverage_percentage']
        })
        backorder_trend.append({
            'Week': week,
            'Backorder Risk': summary['total_backorder_risk']
        })
        shortage_trend.append({
            'Week': week,
            'Shortage Items': summary['items_below_lower']
        })
        excess_trend.append({
            'Week': week,
            'Excess Items': summary['items_above_upper']
        })

    coverage_df = pd.DataFrame(coverage_trend)
    backorder_df = pd.DataFrame(backorder_trend)
    shortage_df = pd.DataFrame(shortage_trend)
    excess_df = pd.DataFrame(excess_trend)

    # Coverage trend
    st.markdown("###  Safety Stock Coverage Trend")

    fig_coverage = px.line(
        coverage_df,
        x='Week',
        y='Coverage %',
        markers=True,
        title="Safety Stock Coverage % (BAL >= LOWER BOUND)"
    )
    fig_coverage.update_traces(line_color='#198754', marker=dict(size=10))
    fig_coverage.update_layout(
        height=300,
        font=dict(family='Nunito, sans-serif', size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_range=[0, 100]
    )
    st.plotly_chart(fig_coverage, use_container_width=True)

    # Current week comparison
    col1, col2 = st.columns(2)

    with col1:
        current_coverage = coverage_df.iloc[-1]['Coverage %']
        prev_coverage = coverage_df.iloc[-2]['Coverage %'] if len(coverage_df) > 1 else current_coverage
        delta = current_coverage - prev_coverage

        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Current Coverage (W6)</h4>
                <div class='kpi-value kpi-positive'>{current_coverage:.1f}%</div>
                <small style='color: {"#198754" if delta >= 0 else "#dc3545"};'>
                    {delta:+.1f}% vs W5
                </small>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        avg_coverage = coverage_df['Coverage %'].mean()
        st.markdown(f"""
            <div class='metric-card'>
                <h4 style='margin: 0; color: #899bbd; font-size: 0.875rem;'>Average Coverage (4 weeks)</h4>
                <div class='kpi-value'>{avg_coverage:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)

    # Backorder risk trend
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Backorder Risk Trend")

    fig_backorder = px.line(
        backorder_df,
        x='Week',
        y='Backorder Risk',
        markers=True,
        title="Total Backorder Risk Cost ($)"
    )
    fig_backorder.update_traces(line_color='#dc3545', marker=dict(size=10))
    fig_backorder.update_layout(
        height=300,
        font=dict(family='Nunito, sans-serif', size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_backorder, use_container_width=True)

    # Shortage vs Excess trend
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Shortage vs Excess Items")

    combined_df = pd.DataFrame({
        'Week': weeks,
        'Shortage Items': shortage_df['Shortage Items'],
        'Excess Items': excess_df['Excess Items']
    })

    fig_balance = go.Figure()
    fig_balance.add_trace(go.Bar(
        x=combined_df['Week'],
        y=combined_df['Shortage Items'],
        name='Shortage Items',
        marker_color='#dc3545'
    ))
    fig_balance.add_trace(go.Bar(
        x=combined_df['Week'],
        y=combined_df['Excess Items'],
        name='Excess Items',
        marker_color='#ffc107'
    ))

    fig_balance.update_layout(
        barmode='group',
        height=300,
        font=dict(family='Nunito, sans-serif', size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title="Inventory Imbalance Trend"
    )
    st.plotly_chart(fig_balance, use_container_width=True)

    # Warehouse performance ranking
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Warehouse Performance Ranking (Week 6)")

    position = get_cached_inventory_position(loader, 'W6')

    if not position.empty:
        # Calculate coverage percentage by warehouse
        wh_performance = position.groupby('WAREHOUSE').apply(
            lambda x: (x['BALANCE'] >= x['LOWER_BOUND']).sum() / len(x) * 100
        ).reset_index()
        wh_performance.columns = ['Warehouse', 'Coverage %']
        wh_performance = wh_performance.sort_values('Coverage %', ascending=False)

        fig_ranking = px.bar(
            wh_performance.head(10),
            x='Coverage %',
            y='Warehouse',
            orientation='h',
            title="Top 10 Warehouses by Coverage %",
            color='Coverage %',
            color_continuous_scale='RdYlGn',
            range_color=[0, 100]
        )
        fig_ranking.update_layout(
            height=400,
            font=dict(family='Nunito, sans-serif', size=12),
            showlegend=False
        )
        st.plotly_chart(fig_ranking, use_container_width=True)

    # Item risk analysis
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Top 10 At-Risk Items (Week 6)")

    shortages = get_cached_shortages(loader, 'W6')

    if not shortages.empty and 'BACKORDER_RISK_COST' in shortages.columns:
        top_risk = shortages.nlargest(10, 'BACKORDER_RISK_COST')

        risk_display = top_risk[[
            'ITEM', 'WAREHOUSE', 'SHORTAGE_QTY', 'BACKORDER_RISK_COST'
        ]].copy()

        risk_display['SHORTAGE_QTY'] = risk_display['SHORTAGE_QTY'].apply(lambda x: f"{x:,.0f}")
        risk_display['BACKORDER_RISK_COST'] = risk_display['BACKORDER_RISK_COST'].apply(lambda x: f"${x:,.2f}")
        risk_display.columns = ['Item', 'Warehouse', 'Shortage Qty', 'Backorder Risk']

        st.dataframe(risk_display, use_container_width=True, hide_index=True)
    else:
        st.success("No at-risk items identified!")


# =============================================================================
# PAGE 6: REPORTS
# =============================================================================

def show_reports_page(loader):
    """Reports and data export page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Reports & Export</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> / <span style='color: #4154f1;'>Reports</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("###  Generate Reports")

    # Week selector
    week = st.selectbox("Select Week for Report", ['W3', 'W4', 'W5', 'W6'], key='report_week')

    # Generate comprehensive report
    if st.button(" Generate Comprehensive Report", type="primary"):
        with st.spinner("Generating report..."):
            summary = get_cached_summary_stats(loader, week)
            shortages = get_cached_shortages(loader, week)
            excess = get_cached_excess(loader, week)
            opportunities = get_cached_transshipment_opportunities(loader, week)

            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("AFI SUPPLY CHAIN DECISION SUPPORT SYSTEM")
            report_lines.append("COMPREHENSIVE ANALYSIS REPORT")
            report_lines.append("=" * 80)
            report_lines.append(f"\nReport Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append(f"Analysis Week: {week}")
            report_lines.append("\n" + "=" * 80)

            report_lines.append("\n## EXECUTIVE SUMMARY")
            report_lines.append(f"Total Warehouses: {summary['total_warehouses']}")
            report_lines.append(f"Total Items: {summary['total_items']}")
            report_lines.append(f"Total SKUs: {summary['total_skus']:,}")
            report_lines.append(f"Safety Stock Coverage: {summary['coverage_percentage']:.1f}%")
            report_lines.append(f"Items Below Safety Stock: {summary['items_below_lower']:,}")
            report_lines.append(f"Items Above Maximum: {summary['items_above_upper']:,}")
            report_lines.append(f"Total Backorder Risk: ${summary['total_backorder_risk']:,.0f}")

            report_lines.append("\n" + "=" * 80)
            report_lines.append("\n## SHORTAGE ANALYSIS")
            if not shortages.empty:
                report_lines.append(f"Total Shortage Items: {len(shortages):,}")
                report_lines.append(f"Total Shortage Quantity: {shortages['SHORTAGE_QTY'].sum():,.0f} units")
                if 'BACKORDER_RISK_COST' in shortages.columns:
                    report_lines.append(f"Total Backorder Risk: ${shortages['BACKORDER_RISK_COST'].sum():,.2f}")
                    report_lines.append("\nTop 10 At-Risk Items:")
                    top_10 = shortages.nlargest(10, 'BACKORDER_RISK_COST')
                    for idx, row in top_10.iterrows():
                        report_lines.append(f"  - {row['ITEM']} @ {row['WAREHOUSE']}: {row['SHORTAGE_QTY']:.0f} units (Risk: ${row['BACKORDER_RISK_COST']:.2f})")
            else:
                report_lines.append("No shortage items identified.")

            report_lines.append("\n" + "=" * 80)
            report_lines.append("\n## EXCESS INVENTORY ANALYSIS")
            if not excess.empty:
                report_lines.append(f"Total Excess Items: {len(excess):,}")
                report_lines.append(f"Total Excess Quantity: {excess['EXCESS_QTY'].sum():,.0f} units")
                report_lines.append("\nTop 10 Excess Items:")
                top_10_excess = excess.nlargest(10, 'EXCESS_QTY')
                for idx, row in top_10_excess.iterrows():
                    report_lines.append(f"  - {row['ITEM']} @ {row['WAREHOUSE']}: {row['EXCESS_QTY']:.0f} units over maximum")
            else:
                report_lines.append("No excess inventory identified.")

            report_lines.append("\n" + "=" * 80)
            report_lines.append("\n## TRANSSHIPMENT OPPORTUNITIES")
            if opportunities:
                report_lines.append(f"Total Opportunities: {len(opportunities)}")
                high_priority = [o for o in opportunities if o['priority'] == 'HIGH']
                report_lines.append(f"High Priority: {len(high_priority)}")
                report_lines.append(f"Total Potential Savings: ${sum(o['net_benefit'] for o in opportunities):,.2f}")
                report_lines.append("\nTop 10 Recommendations:")
                for i, opp in enumerate(opportunities[:10], 1):
                    report_lines.append(f"  {i}. {opp['item']}: {opp['from_warehouse']} → {opp['to_warehouse']}")
                    report_lines.append(f"     Transfer: {opp['transfer_qty']:.0f} units | Net Benefit: ${opp['net_benefit']:.2f}")
            else:
                report_lines.append("No transshipment opportunities identified.")

            report_lines.append("\n" + "=" * 80)
            report_lines.append("\n## RECOMMENDATIONS")
            if summary['items_below_lower'] > 0:
                report_lines.append("WARNING:  CRITICAL: Address shortage items immediately through:")
                report_lines.append("   - Lateral transshipment from excess warehouses")
                report_lines.append("   - Emergency replenishment orders")
                report_lines.append("   - Review safety stock bounds")
            if len(opportunities) > 0:
                report_lines.append(f" OPPORTUNITY: Implement {len(opportunities)} transshipment moves for ${sum(o['net_benefit'] for o in opportunities):,.0f} in savings")
            if summary['coverage_percentage'] >= 90:
                report_lines.append("SUCCESS: EXCELLENT: Safety stock coverage above 90%")
            elif summary['coverage_percentage'] >= 80:
                report_lines.append("✓  GOOD: Safety stock coverage above 80%")
            else:
                report_lines.append("WARNING:  ATTENTION: Safety stock coverage below 80% - review inventory policies")

            report_lines.append("\n" + "=" * 80)
            report_lines.append("END OF REPORT")
            report_lines.append("=" * 80)

            report_text = "\n".join(report_lines)

            st.text_area("Report Preview", report_text, height=400)

            st.download_button(
                label=" Download Report (TXT)",
                data=report_text,
                file_name=f"AFI_Report_{week}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

    # Data exports
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("###  Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(" Export Shortages (CSV)"):
            shortages = get_cached_shortages(loader, week)
            if not shortages.empty:
                csv = shortages.to_csv(index=False)
                st.download_button(
                    label="Download Shortages CSV",
                    data=csv,
                    file_name=f"AFI_Shortages_{week}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No shortage data to export")

        if st.button(" Export Excess Inventory (CSV)"):
            excess = get_cached_excess(loader, week)
            if not excess.empty:
                csv = excess.to_csv(index=False)
                st.download_button(
                    label="Download Excess CSV",
                    data=csv,
                    file_name=f"AFI_Excess_{week}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No excess data to export")

    with col2:
        if st.button(" Export Transshipment Plan (CSV)"):
            opportunities = get_cached_transshipment_opportunities(loader, week)
            if opportunities:
                opp_df = pd.DataFrame(opportunities)
                csv = opp_df.to_csv(index=False)
                st.download_button(
                    label="Download Transshipment CSV",
                    data=csv,
                    file_name=f"AFI_Transshipment_{week}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No transshipment opportunities to export")

        if st.button(" Export Hot List (CSV)"):
            hot_list = loader.get_hot_list_items()
            if not hot_list.empty:
                csv = hot_list.to_csv(index=False)
                st.download_button(
                    label="Download Hot List CSV",
                    data=csv,
                    file_name=f"AFI_HotList.csv",
                    mime="text/csv"
                )
            else:
                st.info("No hot list data to export")

    # Full data export
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(" Export Complete Inventory Position (CSV)", type="primary"):
        position = get_cached_inventory_position(loader, week)
        if not position.empty:
            csv = position.to_csv(index=False)
            st.download_button(
                label="Download Complete Inventory CSV",
                data=csv,
                file_name=f"AFI_Inventory_Position_{week}.csv",
                mime="text/csv"
            )
        else:
            st.info("No inventory position data to export")


# =============================================================================
# PAGE 7: OPTIMIZATION - DESTINATION CHANGE
# =============================================================================

def show_optimization_page(loader):
    """Destination Change Optimization page"""
    st.markdown("""
        <div class='page-title'>
            <h1>Destination Change Optimization</h1>
            <nav class='breadcrumb' style='color: #899bbd; font-size: 0.875rem;'>
                <span>Home</span> \ <span style='color: #4154f1;'>Optimization</span>
            </nav>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='nice-card'>
            <p style='color: #012970; margin-bottom: 0.5rem;'>
                <strong>Objective:</strong> Minimize total supply chain costs by reallocating firm purchase orders
                between warehouses while maintaining total PO quantities.
            </p>
            <p style='color: #899bbd; font-size: 0.875rem; margin-bottom: 0;'>
                This optimization uses Mixed Integer Linear Programming (MILP) with OR-Tools SCIP solver
                to find the best destination allocation for firm POs in Weeks 3-4.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Configuration section
    st.markdown("### Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        alpha = st.slider(
            "Alpha (Week 3 Priority Weight)",
            min_value=1.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Higher alpha gives more weight to Week 3 costs (nearer term priority)"
        )

    with col2:
        pel_cost = st.number_input(
            "Penalty Cost (per fractional unit)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Cost penalty for splitting packages (fractional units)"
        )

    with col3:
        act_cost = st.number_input(
            "Action Cost (per change)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Cost of making a destination change (discourages unnecessary changes)"
        )

    # Store optimization result in session state
    if 'opt_result' not in st.session_state:
        st.session_state.opt_result = None

    # Run optimization button
    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        run_button = st.button(" Run Optimization", type="primary", use_container_width=True)

    if run_button:
        with st.spinner("Running optimization... This may take a few minutes for large datasets."):
            try:
                # Create optimizer
                optimizer = DestinationChangeOptimizer(
                    loader,
                    alpha=alpha,
                    pel_cost=pel_cost if pel_cost > 0 else None,
                    act_cost=act_cost if act_cost > 0 else None
                )

                # Run optimization
                summary = optimizer.optimize(verbose=False)

                if summary:
                    # Store results in session state
                    st.session_state.opt_result = {
                        'optimizer': optimizer,
                        'summary': summary,
                        'timestamp': pd.Timestamp.now()
                    }
                    st.success("Optimization completed successfully!")
                    st.rerun()
                else:
                    st.error("Optimization failed. No solution found.")

            except Exception as e:
                st.error(f"Error during optimization: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # Display results if available
    if st.session_state.opt_result is not None:
        result = st.session_state.opt_result
        optimizer = result['optimizer']
        summary = result['summary']

        st.markdown("---")
        st.markdown("### Optimization Results")

        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Savings",
                f"${summary['Total Savings']:,.2f}",
                f"{summary['Savings %']:.2f}%",
                delta_color="normal"
            )

        with col2:
            st.metric(
                "Baseline Cost",
                f"${summary['Baseline Cost']:,.2f}"
            )

        with col3:
            st.metric(
                "Optimized Cost",
                f"${summary['Optimized Cost']:,.2f}"
            )

        with col4:
            st.metric(
                "Destination Changes",
                f"{summary['Number of Changes']} / {summary['Total PO Lines']}",
                f"{summary['Change %']:.1f}%"
            )

        # Executive Summary Section
        st.markdown("---")

        # Get warehouse breakdown for summary
        wh_breakdown = optimizer.get_warehouse_cost_breakdown()

        # Initialize summary generator (check for API key in session state or environment)
        gemini_api_key = st.session_state.get('gemini_api_key', None)
        summary_gen = SummaryGenerator(api_key=gemini_api_key)

        # Generate summary
        with st.spinner("Generating executive summary..."):
            summary_result = summary_gen.generate_summary(
                summary=summary,
                baseline_cost=optimizer.baseline_cost,
                optimized_cost=optimizer.optimized_cost,
                wh_breakdown=wh_breakdown,
                use_ai=True
            )

        # Render the summary
        render_summary_streamlit(summary_result)

        st.markdown("---")

        # Cost Breakdown Comparison
        st.markdown("### Cost Breakdown Analysis")

        # Create tabs for overall and warehouse-level analysis
        tab1, tab2, tab3 = st.tabs(["Overall Cost Breakdown", "Warehouse Comparison", "Warehouse Details"])

        with tab1:
            cost_df = optimizer.get_cost_breakdown_dataframe()

            # Create comparison chart
            fig_cost = go.Figure()

            # Filter out total row for chart
            cost_chart_df = cost_df[cost_df['Cost Component'] != 'TOTAL']

            fig_cost.add_trace(go.Bar(
                name='Baseline',
                x=cost_chart_df['Cost Component'],
                y=cost_chart_df['Baseline'],
                marker_color='#ff6384',
                text=cost_chart_df['Baseline'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ))

            fig_cost.add_trace(go.Bar(
                name='Optimized',
                x=cost_chart_df['Cost Component'],
                y=cost_chart_df['Optimized'],
                marker_color='#36a2eb',
                text=cost_chart_df['Optimized'].apply(lambda x: f'${x:,.0f}'),
                textposition='outside'
            ))

            fig_cost.update_layout(
                barmode='group',
                title='Overall Cost Comparison: Baseline vs Optimized',
                xaxis_title='Cost Component',
                yaxis_title='Cost ($)',
                template='plotly_white',
                height=500,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig_cost, use_container_width=True)

            # Cost breakdown table
            st.dataframe(
                cost_df.style.format({
                    'Baseline': '${:,.2f}',
                    'Optimized': '${:,.2f}',
                    'Savings': '${:,.2f}',
                    'Savings %': '{:.2f}%'
                }),
                use_container_width=True,
                hide_index=True
            )

        with tab2:
            # Get warehouse-level breakdown
            wh_cost_df = optimizer.get_warehouse_cost_breakdown()

            if not wh_cost_df.empty:
                # Warehouse comparison chart
                fig_wh_compare = go.Figure()

                fig_wh_compare.add_trace(go.Bar(
                    name='Baseline Cost',
                    x=wh_cost_df['Warehouse'],
                    y=wh_cost_df['Baseline Cost'],
                    marker_color='#ff6384',
                    text=wh_cost_df['Baseline Cost'].apply(lambda x: f'${x:,.0f}'),
                    textposition='outside'
                ))

                fig_wh_compare.add_trace(go.Bar(
                    name='Optimized Cost',
                    x=wh_cost_df['Warehouse'],
                    y=wh_cost_df['Optimized Cost'],
                    marker_color='#36a2eb',
                    text=wh_cost_df['Optimized Cost'].apply(lambda x: f'${x:,.0f}'),
                    textposition='outside'
                ))

                fig_wh_compare.update_layout(
                    barmode='group',
                    title='Cost Comparison by Warehouse',
                    xaxis_title='Warehouse',
                    yaxis_title='Cost ($)',
                    template='plotly_white',
                    height=500,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                st.plotly_chart(fig_wh_compare, use_container_width=True)

                # Savings by warehouse chart
                fig_wh_savings = px.bar(
                    wh_cost_df,
                    x='Warehouse',
                    y='Savings',
                    color='Savings %',
                    title='Savings by Warehouse',
                    labels={'Savings': 'Savings ($)', 'Savings %': 'Savings %'},
                    color_continuous_scale='RdYlGn',
                    text=wh_cost_df['Savings'].apply(lambda x: f'${x:,.0f}')
                )

                fig_wh_savings.update_traces(textposition='outside')
                fig_wh_savings.update_layout(
                    template='plotly_white',
                    height=400,
                    xaxis_title='Warehouse',
                    yaxis_title='Savings ($)'
                )

                st.plotly_chart(fig_wh_savings, use_container_width=True)

                # Warehouse comparison table
                st.markdown("#### Warehouse Cost Summary Table")
                st.dataframe(
                    wh_cost_df.style.format({
                        'Baseline Cost': '${:,.2f}',
                        'Optimized Cost': '${:,.2f}',
                        'Savings': '${:,.2f}',
                        'Savings %': '{:.2f}%',
                        'Firm PO Volume': '{:,.0f}',
                        'Num Changes': '{:,.0f}'
                    }).background_gradient(subset=['Savings %'], cmap='RdYlGn', vmin=-5, vmax=30),
                    use_container_width=True,
                    hide_index=True
                )

                # Download warehouse breakdown
                csv_wh = wh_cost_df.to_csv(index=False)
                st.download_button(
                    label=" Download Warehouse Breakdown CSV",
                    data=csv_wh,
                    file_name=f"Warehouse_Cost_Breakdown_{result['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No warehouse-level data available.")

        with tab3:
            # Warehouse selector for detailed analysis
            st.markdown("#### Select Warehouse for Detailed Analysis")

            wh_cost_df = optimizer.get_warehouse_cost_breakdown()

            if not wh_cost_df.empty:
                selected_warehouse = st.selectbox(
                    "Choose Warehouse",
                    options=wh_cost_df['Warehouse'].tolist(),
                    help="Select a warehouse to see detailed cost breakdown and changes"
                )

                if selected_warehouse:
                    # Filter data for selected warehouse
                    wh_data = wh_cost_df[wh_cost_df['Warehouse'] == selected_warehouse].iloc[0]

                    # Display warehouse metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric(
                            f"{selected_warehouse} Baseline Cost",
                            f"${wh_data['Baseline Cost']:,.2f}"
                        )

                    with col2:
                        st.metric(
                            f"{selected_warehouse} Optimized Cost",
                            f"${wh_data['Optimized Cost']:,.2f}"
                        )

                    with col3:
                        st.metric(
                            f"{selected_warehouse} Savings",
                            f"${wh_data['Savings']:,.2f}",
                            f"{wh_data['Savings %']:.2f}%"
                        )

                    with col4:
                        # Calculate % of total savings
                        total_savings = summary['Total Savings']
                        pct_of_total = (wh_data['Savings'] / total_savings * 100) if total_savings > 0 else 0
                        st.metric(
                            "% of Total Savings",
                            f"{pct_of_total:.1f}%"
                        )

                    # Pie chart: Baseline vs Optimized for selected warehouse
                    st.markdown(f"#### {selected_warehouse} Cost Breakdown")

                    fig_wh_pie = go.Figure()

                    fig_wh_pie.add_trace(go.Pie(
                        labels=['Baseline Cost', 'Optimized Cost'],
                        values=[wh_data['Baseline Cost'], wh_data['Optimized Cost']],
                        marker=dict(colors=['#ff6384', '#36a2eb']),
                        hole=0.4,
                        textinfo='label+value+percent',
                        texttemplate='%{label}<br>$%{value:,.0f}<br>(%{percent})'
                    ))

                    fig_wh_pie.update_layout(
                        title=f'{selected_warehouse} - Baseline vs Optimized Cost',
                        template='plotly_white',
                        height=400,
                        showlegend=True
                    )

                    st.plotly_chart(fig_wh_pie, use_container_width=True)

                    # Changes for selected warehouse
                    st.markdown(f"#### Destination Changes for {selected_warehouse}")

                    changes_df = optimizer.get_changes_dataframe()
                    wh_changes = changes_df[changes_df['Warehouse'] == selected_warehouse]

                    if not wh_changes.empty:
                        st.write(f"Total changes for {selected_warehouse}: **{len(wh_changes)}** items")

                        st.dataframe(
                            wh_changes.style.format({
                                'Firm PO': '{:.0f}',
                                'New Pack': '{:.0f}',
                                'New F': '{:.0f}',
                                'New Total': '{:.2f}',
                                'Change': '{:.2f}'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )

                        # Download warehouse-specific changes
                        csv_wh_changes = wh_changes.to_csv(index=False)
                        st.download_button(
                            label=f" Download {selected_warehouse} Changes CSV",
                            data=csv_wh_changes,
                            file_name=f"{selected_warehouse}_Changes_{result['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info(f"No destination changes for {selected_warehouse}. Current allocation is optimal.")
            else:
                st.warning("No warehouse data available.")

        # Destination Changes Log
        st.markdown("### Destination Changes Log")

        changes_df = optimizer.get_changes_dataframe()

        if not changes_df.empty:
            st.write(f"Total changes: **{len(changes_df)}** destination reallocations")

            # Display changes table
            st.dataframe(
                changes_df.style.format({
                    'Firm PO': '{:.0f}',
                    'New Pack': '{:.0f}',
                    'New F': '{:.0f}',
                    'New Total': '{:.2f}',
                    'Change': '{:.2f}'
                }),
                use_container_width=True,
                hide_index=True
            )

            # Export changes to CSV
            csv = changes_df.to_csv(index=False)
            st.download_button(
                label=" Download Changes CSV",
                data=csv,
                file_name=f"AFI_Destination_Changes_{result['timestamp'].strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No destination changes recommended. Current allocation is already optimal.")

        # Summary Report
        st.markdown("### Summary Report")

        summary_text = f"""
**Optimization Summary Report**
Generated: {result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

**Parameters:**
- Alpha (Week 3 Weight): {summary['Alpha']}
- Penalty Cost: ${pel_cost:,.2f}
- Action Cost: ${act_cost:,.2f}

**Results:**
- Baseline Total Cost: ${summary['Baseline Cost']:,.2f}
- Optimized Total Cost: ${summary['Optimized Cost']:,.2f}
- Total Savings: ${summary['Total Savings']:,.2f} ({summary['Savings %']:.2f}%)
- Destination Changes: {summary['Number of Changes']} out of {summary['Total PO Lines']} PO lines ({summary['Change %']:.1f}%)
- Status: {summary['Status']}

**Recommendation:**
{"The optimization found significant cost savings by reallocating firm POs. Implement the recommended changes." if summary['Total Savings'] > 0 else "Current allocation is already optimal. No changes needed."}
        """

        st.text_area("", summary_text, height=400)

        # Download summary report
        st.download_button(
            label=" Download Summary Report",
            data=summary_text,
            file_name=f"AFI_Optimization_Summary_{result['timestamp'].strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


# =============================================================================
# RUN APP
# =============================================================================

if __name__ == "__main__":
    main()
