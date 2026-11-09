"""
Data Cleaning Module for SuperStore Sales Analytics
====================================================

This module handles loading, inspecting, cleaning, and enriching the raw
SuperStore dataset.  It is the first step in the analytics pipeline.

Key responsibilities:
    - Load raw CSV data
    - Inspect data quality (nulls, duplicates, types)
    - Convert date columns to proper datetime
    - Validate numeric fields
    - Engineer analytical features (shipping_days, profit_margin, etc.)
    - Save cleaned data to the processed folder

Author : SuperStore Analytics Project
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "SuperStoreOrders - SuperStoreOrders.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DATA_PATH = PROCESSED_DIR / "superstore_cleaned.csv"

DATE_COLUMNS = ["order_date", "ship_date"]
NUMERIC_COLUMNS = ["sales", "quantity", "discount", "profit", "shipping_cost"]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the raw SuperStore CSV file.

    Parameters
    ----------
    path : Path
        Path to the raw CSV file.

    Returns
    -------
    pd.DataFrame
        Raw dataframe exactly as read from disk.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist at the expected location.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {path}. "
            "Please place the CSV in the data/raw/ directory."
        )
    df = pd.read_csv(path)
    print(f"✅ Loaded raw data: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ---------------------------------------------------------------------------
# Inspection helpers
# ---------------------------------------------------------------------------

def inspect_data(df: pd.DataFrame) -> dict:
    """Return a dictionary summarising key data quality metrics.

    This is intentionally verbose so the notebook / report can reference it.
    """
    info = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "total_missing": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_order_ids": int(df.duplicated(subset=["order_id"]).sum()),
        "unique_order_ids": df["order_id"].nunique(),
        "total_rows": len(df),
    }
    return info


def print_inspection(info: dict) -> None:
    """Pretty-print the inspection dictionary."""
    print("=" * 60)
    print("📋 DATA INSPECTION REPORT")
    print("=" * 60)
    print(f"Shape            : {info['shape'][0]:,} rows × {info['shape'][1]} columns")
    print(f"Total missing    : {info['total_missing']}")
    print(f"Duplicate rows   : {info['duplicate_rows']}")
    print(f"Unique order IDs : {info['unique_order_ids']:,}")
    print(f"Total rows       : {info['total_rows']:,}")
    print(f"  → Rows per order (avg): {info['total_rows'] / info['unique_order_ids']:.1f}")
    print()

    # Missing values detail
    missing = {k: v for k, v in info["missing_values"].items() if v > 0}
    if missing:
        print("⚠️  Columns with missing values:")
        for col, cnt in missing.items():
            pct = cnt / info["shape"][0] * 100
            print(f"   {col:25s} → {cnt:,} ({pct:.2f}%)")
    else:
        print("✅ No missing values found.")
    print()

    # Data types
    print("📊 Column data types:")
    for col, dtype in info["dtypes"].items():
        print(f"   {col:25s} → {dtype}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Cleaning steps
# ---------------------------------------------------------------------------

def convert_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Convert order_date and ship_date to datetime.

    The raw data uses D/M/YYYY format (e.g. '1/1/2011' is January 1st).
    This was verified by checking:
        - The first part of the date goes up to 31 (days, not months).
        - Parsing as D/M/Y gives zero NaT values and zero negative
          shipping days, while M/D/Y gives 31K+ NaT values.

    Why this matters:
        Date columns stored as strings cannot be used for time-series
        analysis, date arithmetic, or filtering by month/quarter/year.
    """
    df = df.copy()
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y")
            print(f"  ✅ Converted '{col}' to datetime (D/M/Y format)")
    return df


def validate_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure numeric columns have the correct dtype.

    Handles comma-separated thousands (e.g. '1,648' → 1648.0).
    Negative values in 'profit' are valid (they represent losses).
    Negative values in 'sales', 'quantity', or 'shipping_cost' would be
    suspicious and worth flagging.
    """
    df = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            # Remove thousand-separator commas before converting
            if hasattr(df[col], "str"):
                df[col] = df[col].str.replace(",", "", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Flag suspicious negatives (but do NOT remove them)
    for col in ["sales", "quantity", "shipping_cost"]:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                print(f"  ⚠️  '{col}' has {neg_count:,} negative values — review recommended")
            else:
                print(f"  ✅ '{col}' — no unexpected negatives")

    # Profit can legitimately be negative
    neg_profit = (df["profit"] < 0).sum()
    total = len(df)
    print(f"  ℹ️  'profit' has {neg_profit:,} negative values ({neg_profit/total*100:.1f}%) "
          "— this is expected (discounts, returns, unprofitable products)")

    return df


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values with appropriate strategies.

    Strategy:
        - For this dataset, missing values are typically minimal.
        - We document what's missing rather than blindly dropping rows.
        - Postal codes and similar identifiers may have legitimate blanks.
    """
    df = df.copy()
    missing_total = df.isnull().sum().sum()

    if missing_total == 0:
        print("  ✅ No missing values to handle")
        return df

    # Report per column
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            pct = missing_count / len(df) * 100
            print(f"  ⚠️  '{col}': {missing_count:,} missing ({pct:.2f}%)")

            # Strategy: for numeric columns, we keep NaN (don't fabricate data)
            # For categorical columns with very few missing, we can fill with 'Unknown'
            if df[col].dtype == "object" and pct < 5:
                df[col] = df[col].fillna("Unknown")
                print(f"       → Filled with 'Unknown'")

    return df


def remove_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove exact duplicate rows (all columns identical).

    IMPORTANT: We do NOT remove rows with duplicate order_id values,
    because a single order can contain multiple products (order lines).
    Only truly identical rows across ALL columns are removed.

    Interview tip:
        'I distinguished between duplicate rows and duplicate order IDs.
         Multiple rows sharing an order_id are valid order lines — different
         products in the same order.  Only rows identical across every
         column are true duplicates.'
    """
    df = df.copy()
    n_before = len(df)
    df = df.drop_duplicates()
    n_after = len(df)
    removed = n_before - n_after

    if removed > 0:
        print(f"  🗑️  Removed {removed:,} exact duplicate rows")
    else:
        print("  ✅ No exact duplicate rows found")

    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create new analytical columns from existing data.

    New columns:
        month          – Month number (1-12)
        quarter        – Quarter number (1-4)
        order_month    – Year-Month string for time-series grouping (e.g. '2011-01')
        shipping_days  – Days between order_date and ship_date
        profit_margin  – profit / sales (as a ratio, not percentage)

    Why these features matter:
        - month / quarter: Enable seasonal analysis.
        - order_month: Clean x-axis labels for time-series charts.
        - shipping_days: Measure fulfillment speed.
        - profit_margin: Normalised profitability independent of order size.
    """
    df = df.copy()

    # Time-based features
    df["month"] = df["order_date"].dt.month
    df["quarter"] = df["order_date"].dt.quarter
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)

    # Shipping days
    df["shipping_days"] = (df["ship_date"] - df["order_date"]).dt.days

    # Flag negative shipping days (ship before order — data quality issue)
    neg_ship = (df["shipping_days"] < 0).sum()
    if neg_ship > 0:
        print(f"  ⚠️  {neg_ship:,} records have negative shipping days (ship before order)")
    else:
        print("  ✅ All shipping days are non-negative")

    # Profit margin (handle division by zero)
    df["profit_margin"] = np.where(
        df["sales"] != 0,
        df["profit"] / df["sales"],
        0.0
    )

    print(f"  ✅ Created features: month, quarter, order_month, shipping_days, profit_margin")

    return df


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Detect and report statistical outliers using the IQR method.

    IMPORTANT: We do NOT remove outliers.  In retail data, extreme values
    are often genuine:
        - Very large orders (bulk / corporate purchases)
        - Negative profits (returns, heavy discounts)
        - High shipping costs (large / heavy items, remote destinations)

    This function only prints a summary for awareness.
    """
    print("\n📊 OUTLIER DETECTION (IQR method — for information only)")
    print("-" * 50)

    for col in ["sales", "profit", "quantity", "discount", "shipping_cost"]:
        if col not in df.columns:
            continue

        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)]

        print(f"  {col:18s} | Q1={q1:>10.2f} | Q3={q3:>10.2f} | "
              f"IQR={iqr:>10.2f} | Outliers: {len(outliers):,}")

    print()
    print("  ℹ️  Outliers are NOT removed — they represent real business data")
    print("     (bulk orders, high-discount promotions, returns, etc.)")
    return df


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def clean_data(save: bool = True) -> pd.DataFrame:
    """Run the complete data cleaning pipeline.

    Steps:
        1. Load raw data
        2. Inspect data quality
        3. Convert date columns
        4. Validate numeric columns
        5. Handle missing values
        6. Remove exact duplicates
        7. Engineer features
        8. Detect outliers (report only)
        9. Save cleaned data

    Parameters
    ----------
    save : bool
        If True, save cleaned data to data/processed/.

    Returns
    -------
    pd.DataFrame
        Cleaned and enriched dataframe.
    """
    print("🔧 SUPERSTORE DATA CLEANING PIPELINE")
    print("=" * 60)

    # Step 1 – Load
    print("\n📥 Step 1: Loading raw data...")
    df = load_raw_data()

    # Step 2 – Inspect
    print("\n🔍 Step 2: Inspecting data quality...")
    info = inspect_data(df)
    print_inspection(info)

    # Step 3 – Convert dates
    print("\n📅 Step 3: Converting date columns...")
    df = convert_dates(df)

    # Step 4 – Validate numerics
    print("\n🔢 Step 4: Validating numeric columns...")
    df = validate_numeric_columns(df)

    # Step 5 – Missing values
    print("\n🕳️  Step 5: Handling missing values...")
    df = handle_missing_values(df)

    # Step 6 – Duplicates
    print("\n🔄 Step 6: Removing exact duplicates...")
    df = remove_exact_duplicates(df)

    # Step 7 – Feature engineering
    print("\n⚙️  Step 7: Engineering analytical features...")
    df = engineer_features(df)

    # Step 8 – Outlier detection
    detect_outliers(df)

    # Step 9 – Save
    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(PROCESSED_DATA_PATH, index=False)
        print(f"\n💾 Cleaned data saved to: {PROCESSED_DATA_PATH}")

    # Final summary
    print("\n" + "=" * 60)
    print("✅ CLEANING COMPLETE")
    print(f"   Rows   : {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   New features: month, quarter, order_month, shipping_days, profit_margin")
    print("=" * 60)

    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    clean_data()
