"""
Social Commerce Analytics & Customer Intelligence Pipeline
Author: Aman Jain (amanjain-31)
Repository: https://github.com/amanjain-31/Meesho-Social-Commerce-Analytics-GMV-Retention-CLV-Analysis-
"""

import argparse
import os
import sys
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set style aesthetics
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#444444'
plt.rcParams['axes.linewidth'] = 1.2

def load_data(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load raw relational CSV datasets with error handling.

    Args:
        data_dir (str): Directory path containing raw CSV files.

    Returns:
        Tuple of pandas DataFrames: (customers, orders, order_items, products, returns, suppliers, reviews)
    """
    print(f"Loading raw CSV datasets from '{data_dir}'...")
    required_files = ['customers.csv', 'orders.csv', 'order_items.csv', 'products.csv', 'returns.csv', 'suppliers.csv', 'reviews.csv']
    
    for fname in required_files:
        fpath = os.path.join(data_dir, fname)
        if not os.path.isfile(fpath):
            print(f"[ERROR] Required dataset file missing: '{fpath}'", file=sys.stderr)
            sys.exit(1)
            
    try:
        customers = pd.read_csv(os.path.join(data_dir, 'customers.csv'))
        orders = pd.read_csv(os.path.join(data_dir, 'orders.csv'))
        order_items = pd.read_csv(os.path.join(data_dir, 'order_items.csv'))
        products = pd.read_csv(os.path.join(data_dir, 'products.csv'))
        returns = pd.read_csv(os.path.join(data_dir, 'returns.csv'))
        suppliers = pd.read_csv(os.path.join(data_dir, 'suppliers.csv'))
        reviews = pd.read_csv(os.path.join(data_dir, 'reviews.csv'))
        return customers, orders, order_items, products, returns, suppliers, reviews
    except Exception as e:
        print(f"[ERROR] Failed to load CSV data: {str(e)}", file=sys.stderr)
        sys.exit(1)

def run_analytics(data_dir: str, assets_dir: str) -> None:
    """Execute end-to-end data analytics and plot visual intelligence charts.

    Args:
        data_dir (str): Input directory containing raw data.
        assets_dir (str): Output directory for saving generated PNG charts.
    """
    os.makedirs(assets_dir, exist_ok=True)
    customers, orders, order_items, products, returns, suppliers, reviews = load_data(data_dir)
    
    # Date parsing
    orders['order_date'] = pd.to_datetime(orders['order_date'])
    orders['year_month'] = orders['order_date'].dt.to_period('M')
    
    delivered_orders = orders[orders['order_status'] == 'Delivered']
    
    # 1. Platform Core KPIs
    total_gmv = delivered_orders['total_amount'].sum()
    aov = delivered_orders['total_amount'].mean()
    total_orders = len(orders)
    delivered_count = len(delivered_orders)
    return_rate = (len(orders[orders['order_status'] == 'Returned']) / total_orders) * 100
    cancel_rate = (len(orders[orders['order_status'] == 'Cancelled']) / total_orders) * 100
    cod_rate = (len(orders[orders['payment_method'] == 'COD']) / total_orders) * 100
    
    repeat_customers = delivered_orders.groupby('customer_id')['order_id'].nunique()
    repeat_rate = (sum(repeat_customers > 1) / len(repeat_customers)) * 100
    
    print("\n=======================================================")
    print("        MEESHO SOCIAL COMMERCE ANALYTICS REPORT        ")
    print("                  Author: Aman Jain                    ")
    print("=======================================================")
    print(f" Total Gross Merchandise Value (GMV): Rs. {total_gmv:,.2f}")
    print(f" Average Order Value (AOV):           Rs. {aov:,.2f}")
    print(f" Total Orders Processed:             {total_orders:,}")
    print(f" Delivered Orders:                   {delivered_count:,}")
    print(f" Return Rate:                        {return_rate:.2f}%")
    print(f" Cancellation Rate:                  {cancel_rate:.2f}%")
    print(f" Cash on Delivery (COD) Adoption:    {cod_rate:.2f}%")
    print(f" Repeat Customer Penetration Rate:   {repeat_rate:.2f}%")
    print("=======================================================\n")
    
    # CHART 1: Monthly GMV & Revenue Trend
    print("Generating Chart 1: Monthly GMV & Order Volume Trend...")
    monthly_summary = delivered_orders.groupby('year_month').agg(
        monthly_gmv=('total_amount', 'sum'),
        order_count=('order_id', 'count')
    ).reset_index()
    monthly_summary['year_month_str'] = monthly_summary['year_month'].astype(str)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    sns.barplot(data=monthly_summary, x='year_month_str', y='monthly_gmv', ax=ax1, color='#00ADB5', alpha=0.85)
    sns.lineplot(data=monthly_summary, x='year_month_str', y='order_count', ax=ax2, color='#FF2E63', marker='o', linewidth=2.5)
    
    ax1.set_title('Monthly Platform GMV (Rs.) & Order Volume Trend', fontsize=15, fontweight='bold', pad=15, color='#EEEEEE')
    ax1.set_xlabel('Month-Year', fontsize=12, labelpad=10, color='#CCCCCC')
    ax1.set_ylabel('Gross Merchandise Value (Rs.)', fontsize=12, color='#00ADB5')
    ax2.set_ylabel('Order Count', fontsize=12, color='#FF2E63')
    ax1.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(assets_dir, 'gmv_monthly_trend.png'), dpi=300)
    plt.close()
    
    # CHART 2: Category Revenue & Profitability
    print("Generating Chart 2: Product Category Revenue Distribution...")
    order_items_merged = order_items.merge(products, on='product_id')
    delivered_order_ids = set(delivered_orders['order_id'])
    delivered_items = order_items_merged[order_items_merged['order_id'].isin(delivered_order_ids)].copy()
    delivered_items['item_revenue'] = delivered_items['quantity'] * delivered_items['price_sold']
    
    cat_summary = delivered_items.groupby('category')['item_revenue'].sum().reset_index().sort_values(by='item_revenue', ascending=False)
    
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=cat_summary, x='item_revenue', y='category', hue='category', palette='magma', legend=False)
    plt.title('Delivered Revenue Breakdown by Product Category', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Revenue (Rs. in Millions)', fontsize=11)
    plt.ylabel('Category', fontsize=11)
    
    # Format labels in Millions
    for p in ax.patches:
        width = p.get_width()
        ax.annotate(f'Rs.{width/1e6:.2f}M', (width * 0.95, p.get_y() + p.get_height() / 2.),
                    ha='right', va='center', fontsize=10, color='white', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(assets_dir, 'category_revenue_distribution.png'), dpi=300)
    plt.close()

    # CHART 3: Customer RFM Segmentation
    print("Generating Chart 3: RFM Customer Value Segmentation...")
    max_date = orders['order_date'].max() + pd.Timedelta(days=1)
    rfm = delivered_orders.groupby('customer_id').agg({
        'order_date': lambda x: (max_date - x.max()).days,
        'order_id': 'count',
        'total_amount': 'sum'
    }).reset_index()
    rfm.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    
    # Score bins
    rfm['R_score'] = pd.qcut(rfm['recency'], 4, labels=[4, 3, 2, 1])
    rfm['F_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    rfm['M_score'] = pd.qcut(rfm['monetary'], 4, labels=[1, 2, 3, 4])
    rfm['RFM_Cell'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)
    
    def assign_segment(df):
        if df['R_score'] >= 3 and df['F_score'] >= 3 and df['M_score'] >= 3:
            return 'Champions / High Value'
        elif df['R_score'] >= 3 and df['F_score'] >= 2:
            return 'Loyal Customers'
        elif df['R_score'] <= 2 and df['F_score'] >= 3:
            return 'At Risk / Need Attention'
        elif df['R_score'] <= 2 and df['F_score'] <= 2:
            return 'Hibernating / Churned'
        else:
            return 'Promising / Recent'
            
    rfm['Segment'] = rfm.apply(assign_segment, axis=1)
    seg_counts = rfm['Segment'].value_counts().reset_index()
    seg_counts.columns = ['Segment', 'Count']
    
    plt.figure(figsize=(9, 6))
    colors = ['#30E3CA', '#11999E', '#E4F9F5', '#FF4B5C', '#F0A500']
    plt.pie(seg_counts['Count'], labels=seg_counts['Segment'], autopct='%1.1f%%', startangle=140, 
            colors=colors, textprops={'fontsize': 11, 'color': 'white', 'weight': 'bold'})
    plt.title('Customer Base RFM Segmentation Distribution', fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(assets_dir, 'rfm_customer_segmentation.png'), dpi=300)
    plt.close()

    # CHART 4: Supplier Return Risk Analysis
    print("Generating Chart 4: Supplier Return Rate Risk Score...")
    orders_with_supplier = orders.merge(order_items[['order_id', 'product_id']], on='order_id')
    orders_with_supplier = orders_with_supplier.merge(products[['product_id', 'supplier_id']], on='product_id')
    
    supplier_orders = orders_with_supplier.groupby('supplier_id').agg(
        total_orders=('order_id', 'nunique'),
        returned_orders=('order_status', lambda x: (x == 'Returned').sum())
    ).reset_index()
    
    supplier_orders = supplier_orders.merge(suppliers[['supplier_id', 'supplier_name', 'supplier_tier']], on='supplier_id')
    supplier_orders['return_rate'] = (supplier_orders['returned_orders'] / supplier_orders['total_orders']) * 100
    
    top_risk_suppliers = supplier_orders[supplier_orders['total_orders'] > 20].sort_values(by='return_rate', ascending=False).head(10)
    
    plt.figure(figsize=(10, 5))
    sns.barplot(data=top_risk_suppliers, x='return_rate', y='supplier_name', hue='supplier_tier', dodge=False, palette='Reds_r')
    plt.title('Top 10 High-Risk Suppliers by Order Return Rate (%)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Return Rate (%)', fontsize=11)
    plt.ylabel('Supplier Name', fontsize=11)
    plt.legend(title='Supplier Tier', loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(assets_dir, 'supplier_return_risk.png'), dpi=300)
    plt.close()

    # CHART 5: Cohort Retention Heatmap
    print("Generating Chart 5: Customer Retention Cohort Matrix...")
    delivered_orders['order_month'] = delivered_orders['order_date'].dt.to_period('M')
    delivered_orders['cohort'] = delivered_orders.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    
    cohort_data = delivered_orders.groupby(['cohort', 'order_month']).agg(n_customers=('customer_id', 'nunique')).reset_index()
    cohort_data['period_number'] = (cohort_data['order_month'] - cohort_data['cohort']).apply(lambda x: x.n)
    
    cohort_pivot = cohort_data.pivot_table(index='cohort', columns='period_number', values='n_customers')
    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100
    
    plt.figure(figsize=(12, 7))
    sns.heatmap(retention_matrix.iloc[:10, :10], annot=True, fmt='.1f', cmap='YlGnBu', cbar_kws={'label': 'Retention Rate (%)'})
    plt.title('Customer Cohort Retention Rate (%) Matrix', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Months Since First Purchase', fontsize=11)
    plt.ylabel('Cohort Month', fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(assets_dir, 'retention_cohort_heatmap.png'), dpi=300)
    plt.close()
    
    plt.close('all')
    print(f"\n[SUCCESS] Analytics pipeline complete! All visual assets generated in '{assets_dir}' directory.")

def main():
    default_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    default_assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
    
    parser = argparse.ArgumentParser(description="Social Commerce Analytics & Customer Intelligence Pipeline")
    parser.add_argument('--data-dir', type=str, default=default_data_dir, help="Path to directory containing raw CSV datasets")
    parser.add_argument('--assets-dir', type=str, default=default_assets_dir, help="Path to directory where output charts will be saved")
    
    args = parser.parse_args()
    run_analytics(data_dir=args.data_dir, assets_dir=args.assets_dir)

if __name__ == '__main__':
    main()
