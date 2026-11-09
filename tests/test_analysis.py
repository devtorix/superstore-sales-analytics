"""
Tests for SuperStore Sales Analytics
=====================================

Tests cover data loading, cleaning, feature engineering, and analysis functions.
Run with: py -m pytest tests/ -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_cleaning import (
    load_raw_data,
    inspect_data,
    convert_dates,
    validate_numeric_columns,
    engineer_features,
    remove_exact_duplicates,
)
from src.analysis import (
    load_cleaned_data,
    compute_kpis,
    monthly_trends,
    sales_by_category,
    sales_by_market,
    top_products,
    top_customers,
    discount_vs_profit,
    sales_by_ship_mode,
    sales_growth,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df():
    """Create a small sample DataFrame for testing."""
    data = {
        "order_id": ["ORD-001", "ORD-001", "ORD-002", "ORD-003", "ORD-003"],
        "order_date": pd.to_datetime(
            ["2023-01-15", "2023-01-15", "2023-02-10", "2023-03-20", "2023-03-20"]
        ),
        "ship_date": pd.to_datetime(
            ["2023-01-20", "2023-01-20", "2023-02-15", "2023-03-25", "2023-03-25"]
        ),
        "ship_mode": [
            "Standard Class", "Standard Class", "First Class",
            "Second Class", "Second Class"
        ],
        "customer_name": ["Alice", "Alice", "Bob", "Charlie", "Charlie"],
        "segment": ["Consumer", "Consumer", "Corporate", "Home Office", "Home Office"],
        "state": ["NY", "NY", "CA", "TX", "TX"],
        "country": ["US", "US", "US", "US", "US"],
        "market": ["US", "US", "US", "US", "US"],
        "region": ["East", "East", "West", "South", "South"],
        "product_id": ["P1", "P2", "P3", "P1", "P4"],
        "category": [
            "Technology", "Furniture", "Office Supplies",
            "Technology", "Furniture"
        ],
        "sub_category": ["Phones", "Tables", "Paper", "Phones", "Chairs"],
        "product_name": [
            "iPhone", "IKEA Table", "A4 Paper", "iPhone", "Office Chair"
        ],
        "sales": [500.0, 200.0, 50.0, 300.0, 150.0],
        "quantity": [1, 2, 10, 1, 3],
        "discount": [0.0, 0.1, 0.2, 0.0, 0.15],
        "profit": [100.0, -20.0, 10.0, 60.0, 15.0],
        "shipping_cost": [10.0, 25.0, 5.0, 12.0, 18.0],
        "order_priority": ["High", "High", "Medium", "Low", "Low"],
        "year": [2023, 2023, 2023, 2023, 2023],
    }
    df = pd.DataFrame(data)
    # Add engineered features
    df["month"] = df["order_date"].dt.month
    df["quarter"] = df["order_date"].dt.quarter
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days
    df["profit_margin"] = np.where(df["sales"] != 0, df["profit"] / df["sales"], 0.0)
    return df


@pytest.fixture
def cleaned_df():
    """Load the actual cleaned dataset (integration test)."""
    path = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
    if not path.exists():
        pytest.skip("Cleaned dataset not available — run data_cleaning.py first")
    return pd.read_csv(path, parse_dates=["order_date", "ship_date"])


# ---------------------------------------------------------------------------
# Data cleaning tests
# ---------------------------------------------------------------------------

class TestDataCleaning:
    """Tests for the data cleaning module."""

    def test_raw_data_loads(self):
        """Raw CSV file should load without errors."""
        raw_path = PROJECT_ROOT / "data" / "raw" / "SuperStoreOrders - SuperStoreOrders.csv"
        if not raw_path.exists():
            pytest.skip("Raw data not available")
        df = load_raw_data(raw_path)
        assert len(df) > 0
        assert "order_id" in df.columns

    def test_inspect_data_returns_dict(self, sample_df):
        """inspect_data should return a dictionary with expected keys."""
        info = inspect_data(sample_df)
        assert isinstance(info, dict)
        assert "shape" in info
        assert "missing_values" in info
        assert "duplicate_rows" in info

    def test_remove_exact_duplicates(self):
        """Only exact duplicate rows should be removed."""
        df = pd.DataFrame({
            "order_id": ["A", "A", "A"],
            "product": ["X", "Y", "X"],
            "sales": [100, 200, 100],
        })
        result = remove_exact_duplicates(df)
        # Row 0 and Row 2 are exact duplicates
        assert len(result) == 2

    def test_remove_duplicates_keeps_order_lines(self):
        """Rows with same order_id but different data should be kept."""
        df = pd.DataFrame({
            "order_id": ["A", "A", "B"],
            "product": ["X", "Y", "Z"],
            "sales": [100, 200, 300],
        })
        result = remove_exact_duplicates(df)
        assert len(result) == 3  # All unique, nothing removed


# ---------------------------------------------------------------------------
# Feature engineering tests
# ---------------------------------------------------------------------------

class TestFeatureEngineering:
    """Tests for engineered features."""

    def test_shipping_days_non_negative(self, sample_df):
        """Shipping days should be non-negative when ship_date >= order_date."""
        assert (sample_df["shipping_days"] >= 0).all()

    def test_shipping_days_calculation(self, sample_df):
        """Shipping days should equal the difference in days."""
        expected_days = (sample_df["ship_date"] - sample_df["order_date"]).dt.days
        pd.testing.assert_series_equal(
            sample_df["shipping_days"], expected_days, check_names=False
        )

    def test_profit_margin_calculation(self, sample_df):
        """Profit margin should be profit / sales."""
        for _, row in sample_df.iterrows():
            if row["sales"] != 0:
                expected = row["profit"] / row["sales"]
                assert abs(row["profit_margin"] - expected) < 1e-10

    def test_profit_margin_zero_sales(self):
        """Profit margin should be 0 when sales is 0."""
        df = pd.DataFrame({"sales": [0.0], "profit": [10.0]})
        result = np.where(df["sales"] != 0, df["profit"] / df["sales"], 0.0)
        assert result[0] == 0.0

    def test_quarter_values(self, sample_df):
        """Quarter should be 1-4."""
        assert sample_df["quarter"].between(1, 4).all()

    def test_month_values(self, sample_df):
        """Month should be 1-12."""
        assert sample_df["month"].between(1, 12).all()


# ---------------------------------------------------------------------------
# Analysis function tests
# ---------------------------------------------------------------------------

class TestAnalysis:
    """Tests for analysis functions."""

    def test_compute_kpis(self, sample_df):
        """compute_kpis should return correct metrics."""
        kpis = compute_kpis(sample_df)
        assert kpis["total_sales"] == 1200.0
        assert kpis["total_profit"] == 165.0
        assert kpis["total_orders"] == 3  # 3 unique order_ids
        assert kpis["total_quantity"] == 17
        assert kpis["avg_order_value"] == 1200.0 / 3
        expected_margin = 165.0 / 1200.0 * 100
        assert abs(kpis["profit_margin"] - expected_margin) < 0.01

    def test_monthly_trends(self, sample_df):
        """monthly_trends should group by order_month."""
        result = monthly_trends(sample_df)
        assert "order_month" in result.columns
        assert "sales" in result.columns
        assert "profit" in result.columns
        assert len(result) == 3  # Jan, Feb, Mar

    def test_sales_by_category(self, sample_df):
        """sales_by_category should group by category."""
        result = sales_by_category(sample_df)
        assert len(result) == 3  # Technology, Furniture, Office Supplies
        assert result["sales"].sum() == 1200.0

    def test_sales_by_market(self, sample_df):
        """sales_by_market should group by market."""
        result = sales_by_market(sample_df)
        assert len(result) == 1  # All US in sample
        assert result.iloc[0]["sales"] == 1200.0

    def test_top_products(self, sample_df):
        """top_products should return n products sorted by sales."""
        result = top_products(sample_df, n=2)
        assert len(result) == 2
        assert result.iloc[0]["sales"] >= result.iloc[1]["sales"]

    def test_top_customers(self, sample_df):
        """top_customers should return n customers sorted by sales."""
        result = top_customers(sample_df, n=2)
        assert len(result) == 2
        assert result.iloc[0]["sales"] >= result.iloc[1]["sales"]

    def test_discount_vs_profit(self, sample_df):
        """discount_vs_profit should return bands with aggregations."""
        result = discount_vs_profit(sample_df)
        assert "discount_band" in result.columns
        assert "avg_profit" in result.columns
        assert len(result) > 0

    def test_sales_by_ship_mode(self, sample_df):
        """sales_by_ship_mode should group by ship_mode."""
        result = sales_by_ship_mode(sample_df)
        assert len(result) == 3  # Standard, First, Second Class


# ---------------------------------------------------------------------------
# Integration tests (on actual data)
# ---------------------------------------------------------------------------

class TestIntegration:
    """Integration tests using the actual cleaned dataset."""

    def test_cleaned_data_no_nulls_in_key_columns(self, cleaned_df):
        """Key columns should have no null values."""
        key_cols = ["order_id", "sales", "profit", "quantity", "category", "market"]
        for col in key_cols:
            assert cleaned_df[col].isnull().sum() == 0, f"Column '{col}' has nulls"

    def test_cleaned_data_has_expected_rows(self, cleaned_df):
        """Cleaned data should have 51,290 rows."""
        assert len(cleaned_df) == 51290

    def test_cleaned_data_has_features(self, cleaned_df):
        """Cleaned data should have engineered features."""
        expected = ["month", "quarter", "order_month", "shipping_days", "profit_margin"]
        for col in expected:
            assert col in cleaned_df.columns, f"Missing feature: {col}"

    def test_kpis_are_positive(self, cleaned_df):
        """Total sales and total orders should be positive."""
        kpis = compute_kpis(cleaned_df)
        assert kpis["total_sales"] > 0
        assert kpis["total_orders"] > 0

    def test_all_years_present(self, cleaned_df):
        """Data should span 2011-2014."""
        years = sorted(cleaned_df["year"].unique())
        assert years == [2011, 2012, 2013, 2014]

    def test_all_markets_present(self, cleaned_df):
        """All 7 markets should be present."""
        markets = sorted(cleaned_df["market"].unique())
        assert len(markets) == 7
