import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent    

PROJECT_DIR = BASE_DIR.parent
# DB path (relative, safe, portable)
DB_PATH = PROJECT_DIR / "Data_base_creation" / "techstore_dw.db"

# Connect to the SQLite database
# Page configuration
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #202022;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Database connection
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Load data with caching
@st.cache_data(ttl=600)
def load_data(query):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# ============================================================================
# SIDEBAR FILTERS (Requirement C: Interactive Filters)
# ============================================================================
st.sidebar.header("🔍 Filters")

# Date Range Filter
st.sidebar.subheader("Date Range")
date_query = """
SELECT MIN(full_date) as min_date, MAX(full_date) as max_date 
FROM Dim_Date
"""
date_range_df = load_data(date_query)

if not date_range_df.empty:
    min_date = pd.to_datetime(date_range_df['min_date'].iloc[0]).date()
    max_date = pd.to_datetime(date_range_df['max_date'].iloc[0]).date()
else:
    min_date = datetime(2023, 1, 1).date()
    max_date = datetime(2025, 12, 31).date()

start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Region Filter
st.sidebar.subheader("Location")
region_query = "SELECT DISTINCT region FROM Dim_Store ORDER BY region"
regions_df = load_data(region_query)
regions = ['All'] + regions_df['region'].tolist() if not regions_df.empty else ['All']
selected_regions = st.sidebar.multiselect("Select Region(s)", regions, default=['All'])

# Store Filter
store_query = "SELECT DISTINCT store_name FROM Dim_Store ORDER BY store_name"
stores_df = load_data(store_query)
stores = ['All'] + stores_df['store_name'].tolist() if not stores_df.empty else ['All']
selected_stores = st.sidebar.multiselect("Select Store(s)", stores, default=['All'])

# Product Category Filter
st.sidebar.subheader("Products")
category_query = "SELECT DISTINCT category_name FROM Dim_Product ORDER BY category_name"
categories_df = load_data(category_query)
categories = ['All'] + categories_df['category_name'].tolist() if not categories_df.empty else ['All']
selected_categories = st.sidebar.multiselect("Select Category(ies)", categories, default=['All'])

# Build WHERE clause based on filters
def build_where_clause():
    where_clauses = []
    
    if 'All' not in selected_regions and len(selected_regions) > 0:
        regions_str = "', '".join(selected_regions)
        where_clauses.append(f"s.region IN ('{regions_str}')")
    
    if 'All' not in selected_stores and len(selected_stores) > 0:
        stores_str = "', '".join(selected_stores)
        where_clauses.append(f"s.store_name IN ('{stores_str}')")
    
    if 'All' not in selected_categories and len(selected_categories) > 0:
        cats_str = "', '".join(selected_categories)
        where_clauses.append(f"p.category_name IN ('{cats_str}')")
    
    return " AND " + " AND ".join(where_clauses) if where_clauses else ""

where_clause = build_where_clause()

# ============================================================================
# MAIN DASHBOARD
# ============================================================================
st.title("📊 Sales Analytics Dashboard")
st.markdown("---")

# ============================================================================
# REQUIREMENT A: GLOBAL KPIs
# ============================================================================
st.header("📈 Global KPIs")

# KPI 1: Total Real Revenue
revenue_query = f"""
SELECT 
    COALESCE(SUM(fs.total_revenue), 0) as total_revenue,
    COUNT(DISTINCT fs.transaction_id) as total_transactions
FROM Fact_Sales fs
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
JOIN Dim_Product p ON fs.product_id = p.product_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
"""

# KPI 2: Net Profit
profit_query = f"""
SELECT 
    COALESCE(SUM(fs.total_revenue), 0) as total_revenue,
    COALESCE(SUM(fs.product_cost_total), 0) as total_cogs,
    COALESCE(SUM(fs.shipping_cost), 0) as total_shipping,
    COALESCE(SUM(fs.marketing_cost_per_sale), 0) as total_marketing,
    COALESCE(SUM(fs.net_profit), 0) as net_profit,
    COALESCE(AVG(fs.profit_margin_percent), 0) as avg_profit_margin
FROM Fact_Sales fs
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
JOIN Dim_Product p ON fs.product_id = p.product_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
"""

# KPI 3: Target Achievement
target_query = f"""
SELECT 
    COALESCE(SUM(fs.total_revenue), 0) as actual_sales,
    COALESCE(SUM(s.target_revenue), 0) as target_sales
FROM Fact_Sales fs
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
JOIN Dim_Product p ON fs.product_id = p.product_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
"""

# KPI 4: Average Sentiment Score
sentiment_query = f"""
SELECT 
    COALESCE(AVG(p.avg_sentiment_score), 0) as avg_sentiment,
    COALESCE(AVG(p.avg_rating), 0) as avg_rating,
    COALESCE(SUM(p.review_count), 0) as total_reviews
FROM Dim_Product p
JOIN Fact_Sales fs ON p.product_id = fs.product_id
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
"""

# Load KPI data
revenue_data = load_data(revenue_query)
profit_data = load_data(profit_query)
target_data = load_data(target_query)
sentiment_data = load_data(sentiment_query)

# Extract values
total_revenue = revenue_data['total_revenue'].iloc[0] if not revenue_data.empty else 0
net_profit = profit_data['net_profit'].iloc[0] if not profit_data.empty else 0
actual_sales = target_data['actual_sales'].iloc[0] if not target_data.empty else 0
target_sales = target_data['target_sales'].iloc[0] if not target_data.empty else 0
target_achievement = (actual_sales / target_sales * 100) if target_sales > 0 else 0
avg_sentiment = sentiment_data['avg_sentiment'].iloc[0] if not sentiment_data.empty else 0
avg_rating = sentiment_data['avg_rating'].iloc[0] if not sentiment_data.empty else 0

# Display KPIs in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 Total Revenue",
        value=f"${total_revenue:,.0f}",
        delta=f"{((actual_sales/target_sales - 1)*100):.1f}% vs target" if target_sales > 0 else "N/A"
    )

with col2:
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    st.metric(
        label="💵 Net Profit",
        value=f"${net_profit:,.0f}",
        delta=f"{profit_margin:.1f}% margin"
    )

with col3:
    st.metric(
        label="🎯 Target Achievement",
        value=f"{target_achievement:.1f}%",
        delta=f"{target_achievement - 100:.1f}%" if target_achievement > 0 else "0%"
    )

with col4:
    st.metric(
        label="⭐ Avg Sentiment",
        value=f"{avg_sentiment:.3f}",
        delta=f"Rating: {avg_rating:.2f}/5"
    )

# Gauge Chart for Target Achievement
st.subheader("🎯 Target Achievement Gauge")
fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=target_achievement,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "Target Achievement %", 'font': {'size': 24}},
    delta={'reference': 100, 'increasing': {'color': "green"}},
    gauge={
        'axis': {'range': [None, 150], 'tickwidth': 1, 'tickcolor': "darkblue"},
        'bar': {'color': "darkblue"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 50], 'color': '#ffcccb'},
            {'range': [50, 80], 'color': '#ffffcc'},
            {'range': [80, 100], 'color': '#90ee90'},
            {'range': [100, 150], 'color': '#006400'}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 100
        }
    }
))
fig_gauge.update_layout(height=300)
st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("---")

# ============================================================================
# REQUIREMENT B: ADVANCED SQL ANALYSIS
# ============================================================================
st.header("📊 Advanced Analytics")

# 1. YTD Growth Analysis
st.subheader("📈 YTD Revenue Growth (Window Functions)")
ytd_query = f"""
SELECT 
    d.year,
    d.month,
    d.month_name,
    DATE(d.year || '-' || printf('%02d', d.month) || '-01') as month_date,
    SUM(fs.total_revenue) as monthly_revenue,
    SUM(SUM(fs.total_revenue)) OVER (
        PARTITION BY d.year 
        ORDER BY d.month 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as ytd_revenue,
    SUM(fs.quantity) as monthly_quantity
FROM Fact_Sales fs
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
JOIN Dim_Product p ON fs.product_id = p.product_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
"""

ytd_data = load_data(ytd_query)

if not ytd_data.empty:
    fig_ytd = go.Figure()
    fig_ytd.add_trace(go.Scatter(
        x=ytd_data['month_date'], 
        y=ytd_data['ytd_revenue'],
        mode='lines+markers',
        name='YTD Revenue',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        fill='tonexty',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    fig_ytd.add_trace(go.Bar(
        x=ytd_data['month_date'],
        y=ytd_data['monthly_revenue'],
        name='Monthly Revenue',
        marker_color='lightblue',
        opacity=0.6
    ))
    fig_ytd.update_layout(
        title="Year-to-Date Revenue Accumulation with Monthly Breakdown",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_ytd, use_container_width=True)
else:
    st.info("No data available for the selected filters.")

# 2. Top Products by Category
st.subheader("🏆 Top 3 Products per Category (Window Functions)")
top_products_query = f"""
WITH RankedProducts AS (
    SELECT 
        p.category_name,
        p.product_name,
        SUM(fs.quantity) as total_quantity,
        SUM(fs.total_revenue) as total_revenue,
        SUM(fs.net_profit) as total_profit,
        ROW_NUMBER() OVER (
            PARTITION BY p.category_name 
            ORDER BY SUM(fs.total_revenue) DESC
        ) as rank
    FROM Fact_Sales fs
    JOIN Dim_Product p ON fs.product_id = p.product_id
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Store s ON fs.store_id = s.store_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    GROUP BY p.category_name, p.product_name
)
SELECT category_name, product_name, total_quantity, total_revenue, total_profit, rank
FROM RankedProducts
WHERE rank <= 3
ORDER BY category_name, rank
"""

top_products = load_data(top_products_query)

if not top_products.empty:
    categories_list = top_products['category_name'].unique()
    num_cols = min(len(categories_list), 3)
    cols = st.columns(num_cols)
    
    for idx, category in enumerate(categories_list):
        cat_data = top_products[top_products['category_name'] == category].sort_values('total_revenue', ascending=True)
        
        with cols[idx % num_cols]:
            fig = go.Figure(go.Bar(
                x=cat_data['total_revenue'],
                y=cat_data['product_name'],
                orientation='h',
                marker=dict(
                    color=cat_data['total_revenue'],
                    colorscale='Viridis',
                    showscale=False
                ),
                text=cat_data['total_revenue'].apply(lambda x: f'${x:,.0f}'),
                textposition='auto'
            ))
            fig.update_layout(
                title=f"{category}",
                xaxis_title="Revenue",
                yaxis_title="",
                height=250,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No product data available for the selected filters.")

# 3. Marketing ROI Analysis
st.subheader("💼 Marketing ROI Analysis")
marketing_roi_query = f"""
SELECT 
    d.year,
    d.month,
    d.month_name,
    DATE(d.year || '-' || printf('%02d', d.month) || '-01') as month_date,
    SUM(fs.marketing_cost_per_sale) as marketing_spend,
    SUM(fs.total_revenue) as revenue_generated,
    SUM(fs.net_profit) as profit,
    CASE 
        WHEN SUM(fs.marketing_cost_per_sale) > 0 
        THEN (SUM(fs.total_revenue) - SUM(fs.marketing_cost_per_sale)) / SUM(fs.marketing_cost_per_sale) * 100
        ELSE 0
    END as roi_percentage
FROM Fact_Sales fs
JOIN Dim_Date d ON fs.date_key = d.date_key
JOIN Dim_Store s ON fs.store_id = s.store_id
JOIN Dim_Product p ON fs.product_id = p.product_id
WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
{where_clause}
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
"""

marketing_data = load_data(marketing_roi_query)

if not marketing_data.empty:
    fig_marketing = go.Figure()
    fig_marketing.add_trace(go.Bar(
        x=marketing_data['month_date'],
        y=marketing_data['marketing_spend'],
        name='Marketing Spend',
        marker_color='indianred'
    ))
    fig_marketing.add_trace(go.Bar(
        x=marketing_data['month_date'],
        y=marketing_data['revenue_generated'],
        name='Revenue Generated',
        marker_color='lightseagreen'
    ))
    fig_marketing.add_trace(go.Scatter(
        x=marketing_data['month_date'],
        y=marketing_data['roi_percentage'],
        name='ROI %',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='gold', width=3),
        marker=dict(size=10)
    ))
    
    fig_marketing.update_layout(
        title="Marketing Spend vs Revenue Generated with ROI",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        yaxis2=dict(
            title="ROI %",
            overlaying='y',
            side='right'
        ),
        barmode='group',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_marketing, use_container_width=True)
    
    # Show summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        total_marketing = marketing_data['marketing_spend'].sum()
        st.metric("Total Marketing Spend", f"${total_marketing:,.0f}")
    with col2:
        total_revenue_from_marketing = marketing_data['revenue_generated'].sum()
        st.metric("Total Revenue Generated", f"${total_revenue_from_marketing:,.0f}")
    with col3:
        overall_roi = ((total_revenue_from_marketing - total_marketing) / total_marketing * 100) if total_marketing > 0 else 0
        st.metric("Overall ROI", f"{overall_roi:.1f}%")
else:
    st.info("No marketing data available for the selected filters.")

# 4. Price Competitiveness Analysis
st.subheader("💲 Price Competitiveness Analysis")
price_comp_query = f"""
SELECT 
    p.product_name,
    p.category_name,
    p.unit_price as our_price,
    p.competitor_price,
    p.Competitor_Product_Name,
    p.profit_margin_percent,
    (p.unit_price - p.competitor_price) as price_diff,
    CASE 
        WHEN p.competitor_price IS NULL THEN 'No Competition Data'
        WHEN p.unit_price > p.competitor_price * 1.1 THEN 'Overpriced'
        WHEN p.unit_price < p.competitor_price * 0.9 THEN 'Underpriced'
        ELSE 'Competitive'
    END as price_status,
    SUM(fs.total_revenue) as sales_revenue
FROM Dim_Product p
LEFT JOIN Fact_Sales fs ON p.product_id = fs.product_id
LEFT JOIN Dim_Date d ON fs.date_key = d.date_key
LEFT JOIN Dim_Store s ON fs.store_id = s.store_id
WHERE p.competitor_price IS NOT NULL
    AND d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
GROUP BY p.product_id, p.product_name, p.category_name, p.unit_price, 
         p.competitor_price, p.Competitor_Product_Name, p.profit_margin_percent
ORDER BY sales_revenue DESC
LIMIT 30
"""

price_data = load_data(price_comp_query)

if not price_data.empty:
    # Calculate price difference percentage
    price_data['price_diff_pct'] = ((price_data['our_price'] - price_data['competitor_price']) / 
                                     price_data['competitor_price'] * 100)
    
    # Create scatter plot
    fig_price = go.Figure()
    
    # Color mapping
    color_map = {'Overpriced': 'red', 'Competitive': 'green', 'Underpriced': 'orange', 'No Competition Data': 'gray'}
    
    for status in price_data['price_status'].unique():
        status_data = price_data[price_data['price_status'] == status]
        fig_price.add_trace(go.Scatter(
            x=status_data['competitor_price'],
            y=status_data['our_price'],
            mode='markers',
            name=status,
            marker=dict(
                size=status_data['sales_revenue'] / status_data['sales_revenue'].max() * 30 + 10,
                color=color_map.get(status, 'blue'),
                line=dict(width=1, color='black'),
                opacity=0.7
            ),
            text=status_data['product_name'],
            hovertemplate='<b>%{text}</b><br>Our Price: $%{y:,.0f}<br>Competitor: $%{x:,.0f}<br>Revenue: $%{customdata:,.0f}<extra></extra>',
            customdata=status_data['sales_revenue']
        ))
    
    # Add diagonal reference line
    max_price = max(price_data['our_price'].max(), price_data['competitor_price'].max())
    fig_price.add_trace(go.Scatter(
        x=[0, max_price],
        y=[0, max_price],
        mode='lines',
        line=dict(dash='dash', color='gray', width=2),
        name='Equal Price Line',
        showlegend=True
    ))
    
    fig_price.update_layout(
        title="Product Price Comparison: Our Price vs Competitors (bubble size = sales revenue)",
        xaxis_title="Competitor Average Price ($)",
        yaxis_title="Our Price ($)",
        height=500,
        hovermode='closest'
    )
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Price Status Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        overpriced = len(price_data[price_data['price_status'] == 'Overpriced'])
        st.metric("🔴 Overpriced Products", overpriced, 
                 delta=f"-${price_data[price_data['price_status']=='Overpriced']['price_diff'].sum():,.0f} vs competitors")
    with col2:
        competitive = len(price_data[price_data['price_status'] == 'Competitive'])
        st.metric("🟢 Competitive Products", competitive)
    with col3:
        underpriced = len(price_data[price_data['price_status'] == 'Underpriced'])
        opportunity = price_data[price_data['price_status']=='Underpriced']['price_diff'].abs().sum()
        st.metric("🟠 Underpriced Products", underpriced, 
                 delta=f"+${opportunity:,.0f} potential revenue")
    with col4:
        avg_margin = price_data['profit_margin_percent'].mean()
        st.metric("📊 Avg Profit Margin", f"{avg_margin:.1f}%")
    
    # Detailed table
    with st.expander("📋 View Detailed Price Comparison"):
        display_cols = ['product_name', 'category_name', 'our_price', 'competitor_price', 
                       'price_diff_pct', 'price_status', 'profit_margin_percent', 'sales_revenue']
        st.dataframe(
            price_data[display_cols].style.format({
                'our_price': '${:,.0f}',
                'competitor_price': '${:,.0f}',
                'price_diff_pct': '{:.1f}%',
                'profit_margin_percent': '{:.1f}%',
                'sales_revenue': '${:,.0f}'
            }).background_gradient(subset=['price_diff_pct'], cmap='RdYlGn_r'),
            use_container_width=True
        )
else:
    st.info("No competitor pricing data available for the selected filters.")

st.markdown("---")

# ============================================================================
# CUSTOM KPIs (3 Additional)
# ============================================================================
st.header("🎯 Custom KPIs")

tab1, tab2, tab3 = st.tabs(["📊 Customer Analytics", "📦 Product Performance", "🌍 Regional Insights"])

with tab1:
    st.subheader("Customer Lifetime Value & Segmentation")
    
    # Customer metrics
    customer_query = f"""
SELECT 
    COUNT(DISTINCT customer_id) as total_customers,
    AVG(customer_revenue) as avg_clv,
    MAX(customer_revenue) as max_clv,
    MIN(customer_revenue) as min_clv
FROM (
    SELECT 
        fs.customer_id,
        SUM(fs.total_revenue) as customer_revenue,
        COUNT(fs.transaction_id) as purchase_count
    FROM Fact_Sales fs
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Store s ON fs.store_id = s.store_id
    JOIN Dim_Product p ON fs.product_id = p.product_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    GROUP BY fs.customer_id
)
"""

    
    customer_data = load_data(customer_query)
    
    col1, col2, col3 = st.columns(3)
    
    if not customer_data.empty:
        with col1:
            st.metric("👥 Total Customers", f"{customer_data['total_customers'].iloc[0]:,.0f}")
        with col2:
            st.metric("💎 Avg Customer Lifetime Value", f"${customer_data['avg_clv'].iloc[0]:,.0f}")
        with col3:
            st.metric("🏆 Max Customer Value", f"${customer_data['max_clv'].iloc[0]:,.0f}")
    
    # Customer segmentation by region
    segment_query = f"""
    SELECT 
        c.region,
        COUNT(DISTINCT fs.customer_id) as customers,
        SUM(fs.total_revenue) as revenue,
        AVG(fs.total_revenue) as avg_transaction_value
    FROM Fact_Sales fs
    JOIN Dim_Customer c ON fs.customer_id = c.customer_id
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Store s ON fs.store_id = s.store_id
    JOIN Dim_Product p ON fs.product_id = p.product_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    GROUP BY c.region
    ORDER BY revenue DESC
    """
    
    segment_data = load_data(segment_query)
    
    if not segment_data.empty:
        fig_segment = go.Figure()
        fig_segment.add_trace(go.Bar(
            x=segment_data['region'],
            y=segment_data['customers'],
            name='Customers',
            yaxis='y',
            marker_color='lightblue'
        ))
        fig_segment.add_trace(go.Scatter(
            x=segment_data['region'],
            y=segment_data['revenue'],
            name='Revenue',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='darkgreen', width=3),
            marker=dict(size=12)
        ))
        
        fig_segment.update_layout(
            title="Customer Distribution & Revenue by Region",
            xaxis_title="Region",
            yaxis=dict(title="Number of Customers"),
            yaxis2=dict(title="Revenue ($)", overlaying='y', side='right'),
            height=350
        )
        st.plotly_chart(fig_segment, use_container_width=True)

with tab2:
    st.subheader("Product Performance & Inventory Insights")
    
    # Product performance metrics
    product_perf_query = f"""
    SELECT 
        p.category_name,
        COUNT(DISTINCT p.product_id) as product_count,
        SUM(fs.quantity) as total_units_sold,
        SUM(fs.total_revenue) as total_revenue,
        AVG(p.profit_margin_percent) as avg_margin,
        AVG(fs.profit_margin_percent) as realized_margin
    FROM Fact_Sales fs
    JOIN Dim_Product p ON fs.product_id = p.product_id
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Store s ON fs.store_id = s.store_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    GROUP BY p.category_name
    ORDER BY total_revenue DESC
    """
    
    product_perf = load_data(product_perf_query)
    
    col1, col2, col3 = st.columns(3)
    
    if not product_perf.empty:
        total_products = product_perf['product_count'].sum()
        total_units = product_perf['total_units_sold'].sum()
        avg_margin_all = product_perf['realized_margin'].mean()
        
        with col1:
            st.metric("📦 Total Products Sold", f"{total_products:,.0f}")
        with col2:
            st.metric("📊 Total Units Sold", f"{total_units:,.0f}")
        with col3:
            st.metric("💹 Avg Realized Margin", f"{avg_margin_all:.1f}%")
        
        # Category performance chart
        fig_category = px.treemap(
            product_perf,
            path=[px.Constant("All Categories"), 'category_name'],
            values='total_revenue',
            color='realized_margin',
            color_continuous_scale='RdYlGn',
            title='Category Revenue Distribution (color = profit margin %)'
        )
        fig_category.update_layout(height=400)
        st.plotly_chart(fig_category, use_container_width=True)

with tab3:
    st.subheader("Regional Performance Comparison")
    
    # Regional performance
    regional_query = f"""
    SELECT 
        s.region,
        COUNT(DISTINCT s.store_id) as store_count,
        SUM(fs.total_revenue) as revenue,
        SUM(fs.net_profit) as profit,
        AVG(fs.profit_margin_percent) as profit_margin,
        COUNT(DISTINCT fs.customer_id) as customers,
        SUM(fs.quantity) as units_sold
    FROM Fact_Sales fs
    JOIN Dim_Store s ON fs.store_id = s.store_id
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Product p ON fs.product_id = p.product_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    GROUP BY s.region
    ORDER BY revenue DESC
    """
    
    regional_data = load_data(regional_query)
    
    if not regional_data.empty:
        # Display metrics
        cols = st.columns(len(regional_data))
        for idx, row in regional_data.iterrows():
            with cols[idx]:
                st.metric(
                    f"📍 {row['region']} Region",
                    f"${row['revenue']:,.0f}",
                    delta=f"{row['profit_margin']:.1f}% margin"
                )
        
        # Regional comparison chart
        fig_regional = go.Figure()
        
        fig_regional.add_trace(go.Bar(
            x=regional_data['region'],
            y=regional_data['revenue'],
            name='Revenue',
            marker_color='lightblue'
        ))
        
        fig_regional.add_trace(go.Scatter(
            x=regional_data['region'],
            y=regional_data['profit_margin'],
            name='Profit Margin %',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=12)
        ))
        
        fig_regional.update_layout(
            title="Regional Revenue & Profit Margin Comparison",
            xaxis_title="Region",
            yaxis=dict(title="Revenue ($)"),
            yaxis2=dict(title="Profit Margin %", overlaying='y', side='right'),
            height=400
        )
        st.plotly_chart(fig_regional, use_container_width=True)
        
        # Regional details table
        with st.expander("📊 Regional Performance Details"):
            st.dataframe(
                regional_data.style.format({
                    'revenue': '${:,.0f}',
                    'profit': '${:,.0f}',
                    'profit_margin': '{:.2f}%',
                    'customers': '{:,.0f}',
                    'units_sold': '{:,.0f}'
                }).background_gradient(subset=['profit_margin'], cmap='RdYlGn'),
                use_container_width=True
            )

st.markdown("---")

# ============================================================================
# DATA TABLE VIEW
# ============================================================================
with st.expander("📋 View Raw Sales Data"):
    st.subheader("Recent Transactions")
    
    raw_data_query = f"""
    SELECT 
        fs.transaction_id,
        d.full_date as date,
        s.store_name,
        s.region,
        p.product_name,
        p.category_name,
        c.full_name as customer,
        fs.quantity,
        fs.total_revenue,
        fs.net_profit,
        fs.profit_margin_percent
    FROM Fact_Sales fs
    JOIN Dim_Date d ON fs.date_key = d.date_key
    JOIN Dim_Store s ON fs.store_id = s.store_id
    JOIN Dim_Product p ON fs.product_id = p.product_id
    JOIN Dim_Customer c ON fs.customer_id = c.customer_id
    WHERE d.full_date BETWEEN '{start_date}' AND '{end_date}'
    {where_clause}
    ORDER BY d.full_date DESC, fs.transaction_id DESC
    LIMIT 100
    """
    
    raw_data = load_data(raw_data_query)
    
    if not raw_data.empty:
        st.dataframe(
            raw_data.style.format({
                'total_revenue': '${:,.2f}',
                'net_profit': '${:,.2f}',
                'profit_margin_percent': '{:.2f}%'
            }),
            use_container_width=True
        )
    else:
        st.info("No transaction data available for the selected filters.")

# Add refresh button
if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()