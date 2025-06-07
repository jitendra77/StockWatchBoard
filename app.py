import streamlit as st
import pandas as pd
import time
from stock_fetcher import StockFetcher
from database import DatabaseManager
import numpy as np

# Configure page
st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

def format_currency(value):
    """Format currency values"""
    return f"${value:.2f}"

def format_change(change, percent_change):
    """Format change values with proper signs and colors"""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f} ({sign}{percent_change:.2f}%)"

def get_change_color(change):
    """Get color based on change value"""
    return "green" if change >= 0 else "red"

def display_stock_card(symbol, data):
    """Display a stock card with formatting in a single compact row"""
    current_price = data['current_price']
    change = data['change']
    percent_change = data['percent_change']
    
    color = get_change_color(change)
    
    # Create compact single-row display
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1.5])
    
    with col1:
        st.markdown(f"**{symbol}**")
    
    with col2:
        st.markdown(f"{format_currency(current_price)}")
    
    with col3:
        st.markdown(f":{color}[{change:+.2f}]")
    
    with col4:
        st.markdown(f":{color}[{percent_change:+.2f}%]")

def main():
    st.title("📈 Stock Dashboard")
    st.markdown("Real-time stock price monitoring with up/down segregation")
    
    # Sidebar controls
    st.sidebar.header("Settings")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.session_state.stock_data = None
    
    # Stock selection
    default_stocks = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 
        'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
        'CRM', 'UBER', 'SPOT', 'TWTR', 'SNAP'
    ]
    
    selected_stocks = st.sidebar.multiselect(
        "Select Stocks to Monitor",
        options=default_stocks,
        default=default_stocks[:10]
    )
    
    if not selected_stocks:
        st.warning("Please select at least one stock to monitor.")
        return
    
    # Initialize stock fetcher and database
    fetcher = StockFetcher()
    db = DatabaseManager()
    
    # Check if we need to fetch new data
    current_time = time.time()
    should_fetch = (
        st.session_state.stock_data is None or
        st.session_state.last_update is None or
        (current_time - st.session_state.last_update) > 30
    )
    
    if should_fetch:
        with st.spinner("Fetching stock data..."):
            try:
                stock_data = fetcher.fetch_stocks(selected_stocks)
                st.session_state.stock_data = stock_data
                st.session_state.last_update = current_time
                
                # Save stock data to database
                db.save_stock_data(stock_data)
            except Exception as e:
                st.error(f"Error fetching stock data: {str(e)}")
                return
    
    stock_data = st.session_state.stock_data
    
    if not stock_data:
        st.error("No stock data available. Please try refreshing.")
        return
    
    # Display last update time
    if st.session_state.last_update:
        update_time = time.strftime("%H:%M:%S", time.localtime(st.session_state.last_update))
        st.caption(f"Last updated: {update_time}")
    
    # Separate stocks into up and down
    up_stocks = {}
    down_stocks = {}
    
    for symbol, data in stock_data.items():
        if data['change'] >= 0:
            up_stocks[symbol] = data
        else:
            down_stocks[symbol] = data
    
    # Display stocks in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Stocks Up")
        if up_stocks:
            # Add column headers
            header_col1, header_col2, header_col3, header_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
            with header_col1:
                st.markdown("**Symbol**")
            with header_col2:
                st.markdown("**Price**")
            with header_col3:
                st.markdown("**Change $**")
            with header_col4:
                st.markdown("**Change %**")
            
            st.markdown("---")
            
            for symbol, data in sorted(up_stocks.items(), key=lambda x: x[1]['percent_change'], reverse=True):
                display_stock_card(symbol, data)
        else:
            st.info("No stocks are up at the moment.")
    
    with col2:
        st.subheader("📉 Stocks Down")
        if down_stocks:
            # Add column headers
            header_col1, header_col2, header_col3, header_col4 = st.columns([1.5, 1.5, 1.5, 1.5])
            with header_col1:
                st.markdown("**Symbol**")
            with header_col2:
                st.markdown("**Price**")
            with header_col3:
                st.markdown("**Change $**")
            with header_col4:
                st.markdown("**Change %**")
            
            st.markdown("---")
            
            for symbol, data in sorted(down_stocks.items(), key=lambda x: x[1]['percent_change']):
                display_stock_card(symbol, data)
        else:
            st.info("No stocks are down at the moment.")
    
    # Summary statistics
    st.subheader("📊 Summary")
    
    total_stocks = len(stock_data)
    up_count = len(up_stocks)
    down_count = len(down_stocks)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Stocks", total_stocks)
    
    with col2:
        st.metric("Stocks Up", up_count, delta=None)
    
    with col3:
        st.metric("Stocks Down", down_count, delta=None)
    
    # Auto-refresh mechanism
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent excessive refreshing
        st.rerun()

if __name__ == "__main__":
    main()
