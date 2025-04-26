
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# Gerçek veriyi yükle
df_all = pd.read_pickle('df_all.pkl')

# Sayfa ayarları
st.set_page_config(page_title="Sales Pipeline Dashboard", layout="wide")

st.title("Sales Pipeline Dashboard")

# --- Sales Funnel ---

deal_stage_counts = df_all['deal_stage'].value_counts().reindex(['Prospecting', 'Engaging', 'Won', 'Lost'], fill_value=0).reset_index()
deal_stage_counts.columns = ['deal_stage', 'count']

st.subheader("Sales Funnel Overview")

funnel_fig = go.Figure(go.Funnel(
    y = deal_stage_counts['deal_stage'],
    x = deal_stage_counts['count'],
    textinfo = "value+percent initial",
    marker={"color": ["#92C7CF", "#AAD7D9", "#FBF9F1", "#E5E1DA"]}
))

selected_points = plotly_events(funnel_fig, click_event=True, hover_event=False)

if selected_points:
    selected_stage = deal_stage_counts.iloc[selected_points[0]['pointIndex']]['deal_stage']
    st.success(f"You clicked: {selected_stage}")
else:
    selected_stage = st.selectbox(
        "Or select a deal stage manually:",
        deal_stage_counts['deal_stage']
    )

# --- KPI Hesaplamaları ---

filtered_df = df_all[df_all['deal_stage'] == selected_stage]

expected_pipeline_value = df_all[
    (df_all['deal_stage'].isin(['Prospecting', 'Engaging'])) &
    (df_all['deal_stage'] == selected_stage)
]['sales_price'].sum()

realized_revenue = df_all[
    (df_all['deal_stage'] == 'Won') &
    (df_all['deal_stage'] == selected_stage)
]['close_value'].sum()

lost_opportunities_value = df_all[
    (df_all['deal_stage'] == 'Lost') &
    (df_all['deal_stage'] == selected_stage)
]['sales_price'].sum()

monthly_trend = (
    filtered_df
    .assign(close_month=pd.to_datetime(filtered_df['close_date']).dt.to_period('M'))
    .groupby('close_month')['sales_price']
    .sum()
    .reset_index()
)

# Conversion Rate
total_won = df_all[df_all['deal_stage'] == 'Won'].shape[0]
total_lost = df_all[df_all['deal_stage'] == 'Lost'].shape[0]

if (total_won + total_lost) == 0:
    conversion_rate = 0.0
else:
    conversion_rate = (total_won / (total_won + total_lost)) * 100

# Average Time to Close
filtered_df['engage_date'] = pd.to_datetime(filtered_df['engage_date'])
filtered_df['close_date'] = pd.to_datetime(filtered_df['close_date'])
filtered_df['days_to_close'] = (filtered_df['close_date'] - filtered_df['engage_date']).dt.days
average_time_to_close = filtered_df['days_to_close'].mean()

# Top Products
top_products = (
    filtered_df
    .groupby('product')['sales_price']
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)

# Pipeline by Region
pipeline_by_region = (
    filtered_df
    .groupby('regional_office')['sales_price']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

# --- KPI Cards ---

st.markdown("### 📈 Key KPIs")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Expected Pipeline", f"${expected_pipeline_value:,.0f}")
col2.metric("Realized Revenue", f"${realized_revenue:,.0f}")
col3.metric("Lost Opportunities", f"${lost_opportunities_value:,.0f}")
col4.metric("Conversion Rate", f"{conversion_rate:.1f}%")
col5.metric("Avg Time to Close", f"{average_time_to_close:.1f} days")

# --- Monthly Trend Line Chart ---

st.markdown("### 📊 Monthly Pipeline Trend")

if not monthly_trend.empty:
    monthly_trend['close_month'] = monthly_trend['close_month'].astype(str)

    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Scatter(
        x=monthly_trend['close_month'],
        y=monthly_trend['sales_price'],
        mode='lines+markers',
        name='Sales Price'
    ))
    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Sales Price",
        template="simple_white"
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
else:
    st.info("No data available for selected stage.")

# --- Top Products Bar Chart ---

st.markdown("### 🛒 Top Products by Pipeline Value")

if not top_products.empty:
    fig_products = go.Figure()
    fig_products.add_trace(go.Bar(
        x=top_products['product'],
        y=top_products['sales_price'],
        marker_color='lightseagreen'
    ))
    fig_products.update_layout(
        xaxis_title="Product",
        yaxis_title="Sales Price",
        template="simple_white"
    )
    st.plotly_chart(fig_products, use_container_width=True)
else:
    st.info("No product data available for selected stage.")

# --- Pipeline by Region Chart ---

st.markdown("### 🗺️ Pipeline Distribution by Regional Office")

if not pipeline_by_region.empty:
    fig_region = go.Figure()
    fig_region.add_trace(go.Bar(
        x=pipeline_by_region['regional_office'],
        y=pipeline_by_region['sales_price'],
        marker_color='lightsalmon'
    ))
    fig_region.update_layout(
        xaxis_title="Regional Office",
        yaxis_title="Sales Price",
        template="simple_white"
    )
    st.plotly_chart(fig_region, use_container_width=True)
else:
    st.info("No regional data available for selected stage.")

st.caption("KPIs and visualizations update dynamically based on selected or clicked deal stage.")
