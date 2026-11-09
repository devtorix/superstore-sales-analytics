"""
Generate Report Figures and Key Metrics
=======================================
Generates high-resolution publication-quality visualisations for:
    reports/figures/*.png
and outputs comprehensive analytical numbers for the business insights report.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "superstore_cleaned.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Set global aesthetic style
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["figure.titlesize"] = 14
plt.rcParams["figure.dpi"] = 300

PRIMARY_COLOR = "#1e3a5f"
ACCENT_BLUE = "#2e86de"
ACCENT_GREEN = "#10ac84"
ACCENT_RED = "#ee5253"
ACCENT_AMBER = "#f39c12"

def load_data():
    return pd.read_csv(DATA_PATH, parse_dates=["order_date", "ship_date"])

def generate_all_figures(df):
    print("🎨 Generating high-resolution figures...")

    # 1. Monthly Sales & Profit Trends
    monthly = df.groupby("order_month").agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()
    
    x = range(len(monthly))
    ax1.plot(x, monthly["sales"] / 1000, color=ACCENT_BLUE, linewidth=2.5, marker="o", markersize=4, label="Sales ($K)")
    ax2.plot(x, monthly["profit"] / 1000, color=ACCENT_GREEN, linewidth=2.5, marker="s", markersize=4, label="Profit ($K)")
    
    ax1.set_title("Monthly Sales and Profit Performance (2011 - 2014)", weight="bold", pad=15)
    ax1.set_xlabel("Order Month")
    ax1.set_ylabel("Total Sales ($ Thousands)", color=ACCENT_BLUE)
    ax2.set_ylabel("Total Profit ($ Thousands)", color=ACCENT_GREEN)
    ax1.set_xticks(x[::3])
    ax1.set_xticklabels(monthly["order_month"][::3], rotation=45, ha="right")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax2.grid(False)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "01_monthly_sales_profit_trends.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 01_monthly_sales_profit_trends.png")

    # 2. Sales and Profit by Category
    cat_summary = df.groupby("category").agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
    cat_summary["margin"] = cat_summary["profit"] / cat_summary["sales"] * 100
    cat_summary = cat_summary.sort_values("sales", ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    sns.barplot(data=cat_summary, x="category", y=cat_summary["sales"] / 1e6, palette=[ACCENT_BLUE, PRIMARY_COLOR, "#48dbfb"], ax=ax1)
    ax1.set_title("Total Sales by Category ($ Millions)", weight="bold")
    ax1.set_ylabel("Sales ($M)")
    ax1.set_xlabel("")
    for p in ax1.patches:
        ax1.annotate(f"${p.get_height():.2f}M", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold", fontsize=11)
        
    sns.barplot(data=cat_summary, x="category", y="margin", palette=[ACCENT_GREEN, ACCENT_AMBER, ACCENT_GREEN], ax=ax2)
    ax2.set_title("Profit Margin % by Category", weight="bold")
    ax2.set_ylabel("Profit Margin (%)")
    ax2.set_xlabel("")
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold", fontsize=11)
        
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "02_sales_and_profit_by_category.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 02_sales_and_profit_by_category.png")

    # 3. Sub-Category Profitability (Highlighting Tables loss)
    subcat = df.groupby(["category", "sub_category"]).agg(sales=("sales", "sum"), profit=("profit", "sum")).reset_index()
    subcat = subcat.sort_values("profit", ascending=True)
    
    colors = [ACCENT_RED if p < 0 else ACCENT_GREEN if p > 50000 else ACCENT_BLUE for p in subcat["profit"]]
    
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(subcat["sub_category"], subcat["profit"] / 1000, color=colors)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Net Profit by Sub-Category ($ Thousands)", weight="bold", pad=12)
    ax.set_xlabel("Net Profit ($K)")
    
    for bar in bars:
        width = bar.get_width()
        ha = "left" if width >= 0 else "right"
        offset = 2 if width >= 0 else -2
        ax.annotate(f"${width:,.1f}K", (width + offset, bar.get_y() + bar.get_height()/2),
                    ha=ha, va="center", fontsize=9, weight="bold")
        
    ax.set_xlim(min(subcat["profit"]/1000) * 1.25, max(subcat["profit"]/1000) * 1.15)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "03_profitability_by_subcategory.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 03_profitability_by_subcategory.png")

    # 4. Market Performance and Margins
    market_perf = df.groupby("market").agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    ).reset_index()
    market_perf["margin"] = market_perf["profit"] / market_perf["sales"] * 100
    market_perf = market_perf.sort_values("sales", ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    
    sns.barplot(data=market_perf, x="market", y=market_perf["sales"] / 1e6, palette="crest", ax=ax1)
    ax1.set_title("Market Sales Volume ($ Millions)", weight="bold")
    ax1.set_ylabel("Sales ($M)")
    ax1.set_xlabel("Global Market")
    for p in ax1.patches:
        ax1.annotate(f"${p.get_height():.2f}M", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold")

    sns.barplot(data=market_perf, x="market", y="margin", palette="viridis", ax=ax2)
    ax2.set_title("Market Profit Margin (%)", weight="bold")
    ax2.set_ylabel("Profit Margin (%)")
    ax2.set_xlabel("Global Market")
    ax2.axhline(market_perf["profit"].sum() / market_perf["sales"].sum() * 100, color="red", linestyle="--", label="Global Avg Margin (11.6%)")
    ax2.legend(loc="upper right")
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "04_market_performance_and_margins.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 04_market_performance_and_margins.png")

    # 5. Discount Impact on Profitability
    bins = [-.001, 0, 0.10, 0.20, 0.30, 0.50, 1.01]
    labels = ["0%\n(No Discount)", "1-10%", "11-20%", "21-30%", "31-50%", "50%+"]
    df["discount_tier"] = pd.cut(df["discount"], bins=bins, labels=labels)
    disc_summary = df.groupby("discount_tier", observed=True).agg(
        avg_profit=("profit", "mean"),
        total_profit=("profit", "sum"),
        order_count=("order_id", "count"),
        margin=("profit_margin", "mean")
    ).reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    bar_colors = [ACCENT_GREEN if p > 20 else ACCENT_AMBER if p > 0 else ACCENT_RED for p in disc_summary["avg_profit"]]
    bars = ax.bar(disc_summary["discount_tier"], disc_summary["avg_profit"], color=bar_colors, edgecolor="black", linewidth=0.5)
    ax.axhline(0, color="black", linestyle="-", linewidth=1)
    ax.set_title("Average Profit per Order Line across Discount Tiers", weight="bold", pad=12)
    ax.set_ylabel("Average Profit ($)")
    ax.set_xlabel("Discount Tier")
    
    for bar in bars:
        h = bar.get_height()
        va = "bottom" if h >= 0 else "top"
        offset = 1.5 if h >= 0 else -3.5
        ax.annotate(f"${h:,.1f}", (bar.get_x() + bar.get_width()/2, h + offset),
                    ha="center", va=va, weight="bold", fontsize=10)
        
    ax.set_ylim(-90, 70)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "05_discount_impact_on_profit.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 05_discount_impact_on_profit.png")

    # 6. Regional Performance Matrix
    reg = df.groupby(["market", "region"]).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index()
    reg["margin"] = reg["profit"] / reg["sales"] * 100
    reg = reg.sort_values("margin", ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [ACCENT_RED if m < 5 else ACCENT_AMBER if m < 10 else ACCENT_GREEN for m in reg["margin"]]
    bars = ax.barh(reg["market"] + " - " + reg["region"], reg["margin"], color=colors)
    ax.axvline(11.6, color="navy", linestyle="--", label="Global Average Margin (11.6%)")
    ax.axvline(0, color="black", linestyle="-", linewidth=0.8)
    ax.set_title("Profit Margin (%) by Global Region (Ranked)", weight="bold", pad=12)
    ax.set_xlabel("Profit Margin (%)")
    ax.legend(loc="lower right")
    
    for bar in bars:
        w = bar.get_width()
        ax.annotate(f"{w:.1f}%", (w + 0.5, bar.get_y() + bar.get_height()/2),
                    va="center", fontsize=8.5, weight="bold")
        
    ax.set_xlim(-1, 30)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "06_regional_profit_margin_tiers.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 06_regional_profit_margin_tiers.png")

    # 7. Customer Segment Comparison
    seg = df.groupby("segment").agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("order_id", "nunique")
    ).reset_index()
    seg["margin"] = seg["profit"] / seg["sales"] * 100
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    wedges, texts, autotexts = ax1.pie(seg["sales"], labels=seg["segment"], autopct="%1.1f%%",
                                       colors=[PRIMARY_COLOR, ACCENT_BLUE, "#48dbfb"], startangle=140,
                                       textprops={"weight": "bold"})
    ax1.set_title("Sales Share by Customer Segment", weight="bold")
    
    sns.barplot(data=seg, x="segment", y="margin", palette=[PRIMARY_COLOR, ACCENT_BLUE, "#48dbfb"], ax=ax2)
    ax2.set_title("Profit Margin % by Segment", weight="bold")
    ax2.set_ylabel("Profit Margin (%)")
    ax2.set_xlabel("")
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold")
    ax2.set_ylim(0, 15)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "07_customer_segment_analysis.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 07_customer_segment_analysis.png")

    # 8. Shipping Mode & Fulfillment
    ship = df.groupby("ship_mode").agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        avg_days=("shipping_days", "mean"),
        avg_cost=("shipping_cost", "mean"),
        orders=("order_id", "nunique")
    ).reset_index().sort_values("orders", ascending=False)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    sns.barplot(data=ship, x="ship_mode", y="orders", palette="Blues_r", ax=ax1)
    ax1.set_title("Order Volume by Shipping Mode", weight="bold")
    ax1.set_ylabel("Total Orders")
    ax1.set_xlabel("")
    for p in ax1.patches:
        ax1.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold")
        
    sns.barplot(data=ship, x="ship_mode", y="avg_days", palette="Blues", ax=ax2)
    ax2.set_title("Average Delivery Days by Shipping Mode", weight="bold")
    ax2.set_ylabel("Average Days to Ship")
    ax2.set_xlabel("")
    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.1f} d", (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                     ha="center", va="center", color="white", weight="bold")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "08_shipping_mode_and_cost.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 08_shipping_mode_and_cost.png")

    # 9. Seasonality by Month
    monthly_agg = df.groupby("month").agg(
        avg_sales=("sales", "mean"),
        total_sales=("sales", "sum"),
        total_profit=("profit", "sum")
    ).reset_index()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_agg["month_name"] = month_names

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=monthly_agg, x="month_name", y=monthly_agg["total_sales"] / 1000, palette="mako", ax=ax)
    ax.set_title("Aggregate Sales Seasonality by Month (2011 - 2014 Cumulative)", weight="bold", pad=12)
    ax.set_ylabel("Total Sales ($ Thousands)")
    ax.set_xlabel("Calendar Month")
    for p in ax.patches:
        ax.annotate(f"${int(p.get_height()):,}K", (p.get_x() + p.get_width()/2., p.get_height() + 25),
                    ha="center", va="bottom", fontsize=8, rotation=35)
    ax.set_ylim(0, max(monthly_agg["total_sales"] / 1000) * 1.15)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "09_monthly_seasonality.png", dpi=300)
    plt.close()
    print("  ✅ Saved: 09_monthly_seasonality.png")

    print(f"🎉 All 9 publication figures saved successfully to: {FIGURES_DIR}")

if __name__ == "__main__":
    df = load_data()
    generate_all_figures(df)
