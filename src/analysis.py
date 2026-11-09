"""
Analysis Module for SuperStore Sales Analytics
================================================

Reusable functions for computing business metrics and aggregations.
Used by both the Jupyter notebook (EDA) and the Streamlit dashboard.

Design principle:
    Every function takes a DataFrame and returns either a value or a
    DataFrame — never modifies the input in place.  This makes the
    functions safe to call from interactive widgets with filters.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_cleaned_data(path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """Load the cleaned SuperStore dataset.

    Parses date columns and sets correct dtypes.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned data not found at {path}. "
            "Run src/data_cleaning.py first."
        )
    df = pd.read_csv(path, parse_dates=["order_date", "ship_date"])
    return df


# ---------------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute headline KPIs from the dataset.

    Returns
    -------
    dict with keys:
        total_sales, total_profit, total_orders, total_quantity,
        avg_order_value, profit_margin
    """
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    total_quantity = df["quantity"].sum()
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

    return {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_orders": total_orders,
        "total_quantity": total_quantity,
        "avg_order_value": avg_order_value,
        "profit_margin": profit_margin,
    }


# ---------------------------------------------------------------------------
# Time-series analysis
# ---------------------------------------------------------------------------

def monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales and profit by order_month."""
    result = (
        df.groupby("order_month", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
        )
        .sort_values("order_month")
    )
    return result


def yearly_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate sales and profit by year."""
    result = (
        df.groupby("year", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
        )
        .sort_values("year")
    )
    return result


# ---------------------------------------------------------------------------
# Product analysis
# ---------------------------------------------------------------------------

def sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and profit by product category."""
    return (
        df.groupby("category", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             quantity=("quantity", "sum"))
        .sort_values("sales", ascending=False)
    )


def sales_by_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and profit by sub-category."""
    return (
        df.groupby("sub_category", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             quantity=("quantity", "sum"))
        .sort_values("sales", ascending=False)
    )


def top_products(df: pd.DataFrame, n: int = 10,
                 by: str = "sales") -> pd.DataFrame:
    """Top N products by sales or profit."""
    return (
        df.groupby("product_name", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             quantity=("quantity", "sum"))
        .sort_values(by, ascending=False)
        .head(n)
    )


def loss_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Products with the largest losses (most negative profit)."""
    return (
        df.groupby("product_name", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             quantity=("quantity", "sum"))
        .sort_values("profit", ascending=True)
        .head(n)
    )


# ---------------------------------------------------------------------------
# Geographic analysis
# ---------------------------------------------------------------------------

def sales_by_market(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and profit by market."""
    return (
        df.groupby("market", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             orders=("order_id", "nunique"))
        .sort_values("sales", ascending=False)
    )


def sales_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and profit by region."""
    return (
        df.groupby("region", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             orders=("order_id", "nunique"))
        .sort_values("sales", ascending=False)
    )


def sales_by_country(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N countries by sales."""
    return (
        df.groupby("country", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"))
        .sort_values("sales", ascending=False)
        .head(n)
    )


# ---------------------------------------------------------------------------
# Customer analysis
# ---------------------------------------------------------------------------

def sales_by_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and profit by customer segment."""
    return (
        df.groupby("segment", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             orders=("order_id", "nunique"))
        .sort_values("sales", ascending=False)
    )


def top_customers(df: pd.DataFrame, n: int = 10,
                  by: str = "sales") -> pd.DataFrame:
    """Top N customers by sales or profit."""
    return (
        df.groupby("customer_name", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"),
             orders=("order_id", "nunique"))
        .sort_values(by, ascending=False)
        .head(n)
    )


# ---------------------------------------------------------------------------
# Discount analysis
# ---------------------------------------------------------------------------

def discount_vs_profit(df: pd.DataFrame) -> pd.DataFrame:
    """Average profit and profit margin by discount level.

    Groups discounts into bands: 0%, 1-10%, 11-20%, 21-30%, 31-50%, 50%+.
    """
    df = df.copy()
    bins = [-.001, 0, 0.10, 0.20, 0.30, 0.50, 1.01]
    labels = ["0%", "1-10%", "11-20%", "21-30%", "31-50%", "50%+"]
    df["discount_band"] = pd.cut(df["discount"], bins=bins, labels=labels)

    return (
        df.groupby("discount_band", observed=True)
        .agg(
            avg_profit=("profit", "mean"),
            avg_margin=("profit_margin", "mean"),
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            count=("order_id", "count"),
        )
        .reset_index()
    )


# ---------------------------------------------------------------------------
# Shipping analysis
# ---------------------------------------------------------------------------

def sales_by_ship_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Sales and profit by shipping mode."""
    return (
        df.groupby("ship_mode", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            avg_shipping_days=("shipping_days", "mean"),
            avg_shipping_cost=("shipping_cost", "mean"),
            orders=("order_id", "nunique"),
        )
        .sort_values("sales", ascending=False)
    )


def order_priority_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Sales and profit by order priority."""
    return (
        df.groupby("order_priority", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            avg_shipping_days=("shipping_days", "mean"),
        )
        .sort_values("sales", ascending=False)
    )


# ---------------------------------------------------------------------------
# Sales growth
# ---------------------------------------------------------------------------

def sales_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Year-over-year sales growth."""
    yearly = yearly_trends(df)
    yearly["prev_sales"] = yearly["sales"].shift(1)
    yearly["growth_pct"] = (
        (yearly["sales"] - yearly["prev_sales"]) / yearly["prev_sales"] * 100
    )
    return yearly
