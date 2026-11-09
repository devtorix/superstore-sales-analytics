"""
SuperStore Sales Analytics Dashboard
=====================================

Interactive Streamlit dashboard for exploring global retail performance
metrics across markets, regions, categories, and customer segments.

Run with:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow imports from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analysis import (
    compute_kpis,
    discount_vs_profit,
    monthly_trends,
    sales_by_category,
    sales_by_market,
    sales_by_region,
    sales_by_segment,
    sales_by_subcategory,
    top_customers,
    top_products,
)

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SuperStore Sales Analytics",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Color palette & Plotly defaults
# ---------------------------------------------------------------------------
COLORS = ["#1e3a5f", "#2e86de", "#48dbfb", "#0abde3", "#10ac84", "#1dd1a1"]
PLOTLY_TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* KPI card styling */
    div[data-testid="stMetric"] {
        background-color: #f0f4f8;
        border: 1px solid #d6e4f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(30, 58, 95, 0.08);
    }
    div[data-testid="stMetric"] label {
        color: #1e3a5f;
        font-weight: 600;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #2e86de;
        font-size: 1.6rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f7fafd;
    }
    section[data-testid="stSidebar"] h2 {
        color: #1e3a5f;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #8395a7;
        padding: 24px 0 12px 0;
        font-size: 0.85rem;
        border-top: 1px solid #e8ecf1;
        margin-top: 48px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"


@st.cache_data(show_spinner="Loading data …")
def load_data() -> pd.DataFrame:
    """Load the cleaned SuperStore dataset with parsed dates."""
    df = pd.read_csv(DATA_PATH, parse_dates=["order_date", "ship_date"])
    return df


df_raw = load_data()

# ---------------------------------------------------------------------------
# Helper — currency formatting
# ---------------------------------------------------------------------------


def fmt_currency(value: float) -> str:
    """Format a numeric value as a human-readable currency string."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.1f}K"
    return f"{sign}${abs_val:,.0f}"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center; color:#1e3a5f;'>🏪 SuperStore Sales Analytics</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#576574; font-size:1.1rem; margin-bottom:32px;'>"
    "Global Retail Performance &amp; Business Intelligence Dashboard</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 🔍 Filters")

# Unique values for each filter dimension
all_years = sorted(df_raw["year"].unique())
all_markets = sorted(df_raw["market"].unique())
all_regions = sorted(df_raw["region"].unique())
all_categories = sorted(df_raw["category"].unique())
all_segments = sorted(df_raw["segment"].unique())
all_ship_modes = sorted(df_raw["ship_mode"].unique())

sel_years = st.sidebar.multiselect("📅 Year", all_years, default=all_years)
sel_markets = st.sidebar.multiselect("🌍 Market", all_markets, default=all_markets)
sel_regions = st.sidebar.multiselect("📍 Region", all_regions, default=all_regions)
sel_categories = st.sidebar.multiselect("📦 Category", all_categories, default=all_categories)
sel_segments = st.sidebar.multiselect("👥 Segment", all_segments, default=all_segments)
sel_ship_modes = st.sidebar.multiselect("🚚 Ship Mode", all_ship_modes, default=all_ship_modes)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
df = df_raw.copy()
if sel_years:
    df = df[df["year"].isin(sel_years)]
if sel_markets:
    df = df[df["market"].isin(sel_markets)]
if sel_regions:
    df = df[df["region"].isin(sel_regions)]
if sel_categories:
    df = df[df["category"].isin(sel_categories)]
if sel_segments:
    df = df[df["segment"].isin(sel_segments)]
if sel_ship_modes:
    df = df[df["ship_mode"].isin(sel_ship_modes)]

# Handle empty filtered data
if df.empty:
    st.warning("⚠️ No data matches the selected filters. Please adjust your selections.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
kpis = compute_kpis(df)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Sales", fmt_currency(kpis["total_sales"]))
k2.metric("📈 Total Profit", fmt_currency(kpis["total_profit"]))
k3.metric("📦 Total Orders", f"{kpis['total_orders']:,}")
k4.metric("📊 Profit Margin", f"{kpis['profit_margin']:.1f}%")
k5.metric("🛒 Avg Order Value", fmt_currency(kpis["avg_order_value"]))

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------


def _apply_layout(fig, title: str = "", height: int = 420):
    """Apply consistent layout to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#1e3a5f")),
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=dict(l=40, r=20, t=50, b=40),
        font=dict(family="Inter, sans-serif", size=12, color="#333"),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


# ---------------------------------------------------------------------------
# Row 1 — Monthly Sales & Profit Trends
# ---------------------------------------------------------------------------
st.subheader("📈 Monthly Trends")
trends = monthly_trends(df)

col1, col2 = st.columns(2)

with col1:
    fig = px.line(
        trends,
        x="order_month",
        y="sales",
        labels={"order_month": "Month", "sales": "Sales ($)"},
        color_discrete_sequence=[COLORS[1]],
    )
    fig.update_traces(line=dict(width=2.5), hovertemplate="Month: %{x}<br>Sales: $%{y:,.0f}")
    _apply_layout(fig, "Monthly Sales Trend")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(
        trends,
        x="order_month",
        y="profit",
        labels={"order_month": "Month", "profit": "Profit ($)"},
        color_discrete_sequence=[COLORS[4]],
    )
    fig.update_traces(line=dict(width=2.5), hovertemplate="Month: %{x}<br>Profit: $%{y:,.0f}")
    _apply_layout(fig, "Monthly Profit Trend")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 2 — Category & Sub-Category
# ---------------------------------------------------------------------------
st.subheader("📦 Product Performance")
col1, col2 = st.columns(2)

with col1:
    cat_df = sales_by_category(df)
    fig = px.bar(
        cat_df,
        x="category",
        y="sales",
        color="category",
        text_auto="$.3s",
        labels={"category": "Category", "sales": "Sales ($)"},
        color_discrete_sequence=COLORS,
    )
    fig.update_traces(hovertemplate="Category: %{x}<br>Sales: $%{y:,.0f}")
    fig.update_layout(showlegend=False)
    _apply_layout(fig, "Sales by Category")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    subcat_df = sales_by_subcategory(df)
    fig = px.bar(
        subcat_df,
        x="profit",
        y="sub_category",
        orientation="h",
        color="profit",
        color_continuous_scale=["#e74c3c", "#f39c12", "#10ac84"],
        labels={"sub_category": "Sub-Category", "profit": "Profit ($)"},
    )
    fig.update_traces(hovertemplate="Sub-Category: %{y}<br>Profit: $%{x:,.0f}")
    fig.update_layout(coloraxis_showscale=False)
    _apply_layout(fig, "Profit by Sub-Category")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 3 — Market & Region
# ---------------------------------------------------------------------------
st.subheader("🌍 Geographic Performance")
col1, col2 = st.columns(2)

with col1:
    mkt_df = sales_by_market(df)
    fig = px.bar(
        mkt_df,
        x="market",
        y="sales",
        color="market",
        text_auto="$.3s",
        labels={"market": "Market", "sales": "Sales ($)"},
        color_discrete_sequence=COLORS,
    )
    fig.update_traces(hovertemplate="Market: %{x}<br>Sales: $%{y:,.0f}")
    fig.update_layout(showlegend=False)
    _apply_layout(fig, "Sales by Market")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    reg_df = sales_by_region(df)
    fig = px.bar(
        reg_df,
        x="profit",
        y="region",
        orientation="h",
        color="profit",
        color_continuous_scale=["#e74c3c", "#f39c12", "#10ac84"],
        labels={"region": "Region", "profit": "Profit ($)"},
    )
    fig.update_traces(hovertemplate="Region: %{y}<br>Profit: $%{x:,.0f}")
    fig.update_layout(coloraxis_showscale=False)
    _apply_layout(fig, "Profit by Region", height=480)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 4 — Segment & Discount vs Profit
# ---------------------------------------------------------------------------
st.subheader("👥 Customer Insights")
col1, col2 = st.columns(2)

with col1:
    seg_df = sales_by_segment(df)
    fig = px.pie(
        seg_df,
        values="sales",
        names="segment",
        color_discrete_sequence=COLORS,
        hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="Segment: %{label}<br>Sales: $%{value:,.0f}<br>Share: %{percent}",
    )
    _apply_layout(fig, "Sales by Customer Segment")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    disc_df = discount_vs_profit(df)
    fig = px.scatter(
        disc_df,
        x="discount_band",
        y="avg_profit",
        size="count",
        color="avg_margin",
        color_continuous_scale=["#e74c3c", "#f39c12", "#10ac84"],
        labels={
            "discount_band": "Discount Band",
            "avg_profit": "Avg Profit ($)",
            "avg_margin": "Avg Margin",
            "count": "Orders",
        },
    )
    fig.update_traces(
        hovertemplate=(
            "Discount: %{x}<br>"
            "Avg Profit: $%{y:,.2f}<br>"
            "Orders: %{marker.size:,}"
        )
    )
    _apply_layout(fig, "Discount vs Profit")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Row 5 — Top Products & Top Customers
# ---------------------------------------------------------------------------
st.subheader("🏆 Top Performers")
col1, col2 = st.columns(2)

with col1:
    top_prod = top_products(df, n=10, by="sales")
    fig = px.bar(
        top_prod,
        x="sales",
        y="product_name",
        orientation="h",
        color_discrete_sequence=[COLORS[1]],
        labels={"product_name": "Product", "sales": "Sales ($)"},
    )
    fig.update_traces(hovertemplate="Product: %{y}<br>Sales: $%{x:,.0f}")
    fig.update_yaxes(categoryorder="total ascending")
    _apply_layout(fig, "Top 10 Products by Sales", height=480)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    top_cust = top_customers(df, n=10, by="sales")
    fig = px.bar(
        top_cust,
        x="sales",
        y="customer_name",
        orientation="h",
        color_discrete_sequence=[COLORS[4]],
        labels={"customer_name": "Customer", "sales": "Sales ($)"},
    )
    fig.update_traces(hovertemplate="Customer: %{y}<br>Sales: $%{x:,.0f}")
    fig.update_yaxes(categoryorder="total ascending")
    _apply_layout(fig, "Top 10 Customers by Sales", height=480)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="footer">Built with Streamlit &amp; Plotly | SuperStore Sales Analytics</div>',
    unsafe_allow_html=True,
)
