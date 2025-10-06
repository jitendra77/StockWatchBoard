import streamlit as st
import pandas as pd
import time
from stock_fetcher import StockFetcher
from database import DatabaseManager
from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
from news_simulator import NewsSimulator
from options_analyzer import OptionsAnalyzer
from portfolio_optimizer import PortfolioOptimizer
import numpy as np

# Configure page
st.set_page_config(page_title="Stock Dashboard",
                   page_icon="📈",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'stock_data' not in st.session_state:
    st.session_state.stock_data = None
if 'auto_refresh' not in st.session_state:
#    st.session_state.auto_refresh = True
    st.session_state.auto_refresh = False


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


def display_stock_card(symbol, data, sentiment_data=None):
    """Display a stock card with formatting in a single compact row"""
    current_price = data['current_price']
    change = data['change']
    percent_change = data['percent_change']

    color = get_change_color(change)

    # Create compact single-row display with sentiment
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.8])

    with col1:
        st.markdown(f"**{symbol}**")

    with col2:
        st.markdown(f"{format_currency(current_price)}")

    with col3:
        st.markdown(f":{color}[{change:+.2f}]")

    with col4:
        st.markdown(f":{color}[{percent_change:+.2f}%]")

    with col5:
        if sentiment_data:
            sentiment_score = sentiment_data.get('avg_sentiment', 3.0)
            sentiment_color = "green" if sentiment_score >= 3.5 else "red" if sentiment_score < 2.5 else "gray"
            st.markdown(f":{sentiment_color}[{sentiment_score:.1f}★]")
        else:
            st.markdown("—")


def main():
    st.title("📈 Stock Dashboard")
    st.markdown("Real-time monitoring with sentiment analysis")

    # Sidebar controls
    st.sidebar.header("Settings")

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (300s)",
                                       value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.session_state.stock_data = None

    # Feature toggles
    enable_news = st.sidebar.checkbox("Enable News Sentiment Analysis",
                                      value=True)
    st.sidebar.caption(
        "Note: News analysis covers up to 5 stocks with realistic sentiment data"
    )

    enable_options = st.sidebar.checkbox("Enable CSP Options Analysis",
                                         value=True)
    st.sidebar.caption(
        "Note: Cash Secured Put options with delta 0.15-0.25, expiring within 10 days"
    )

    enable_cc = st.sidebar.checkbox("Enable Covered Call Analysis",
                                    value=True)
    st.sidebar.caption(
        "Note: Covered Calls with delta 0.15-0.25, expiring within 10 days (assumes 100 shares)"
    )

    enable_portfolio_optimization = st.sidebar.checkbox(
        "Enable Portfolio Optimization", value=True)
    st.sidebar.caption(
        "Note: Optimize $100k allocation across AMZN, AAPL, GOOGL, HOOD with same expiry"
    )

    # Stock selection
    default_stocks = [
        'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'NVDA', 'ORCL', 'HOOD', 'PLTR',
        'AVGO'
    ]

    selected_stocks = st.sidebar.multiselect("Select Stocks to Monitor",
                                             options=default_stocks,
                                             default=default_stocks[:8])

    if not selected_stocks:
        st.warning("Please select at least one stock to monitor.")
        return

    # Initialize components
    fetcher = StockFetcher()
    db = DatabaseManager()
    news_fetcher = NewsFetcher()
    sentiment_analyzer = SentimentAnalyzer()
    news_simulator = NewsSimulator()
    options_analyzer = OptionsAnalyzer()
    portfolio_optimizer = PortfolioOptimizer()

    # Check if we need to fetch new data
    current_time = time.time()
    should_fetch = (st.session_state.stock_data is None
                    or st.session_state.last_update is None
                    or (current_time - st.session_state.last_update) > 300)

    if should_fetch:
        with st.spinner("Fetching stock data..."):
            try:
                stock_data = fetcher.fetch_stocks(selected_stocks)
                st.session_state.stock_data = stock_data
                st.session_state.last_update = current_time

                # Save stock data to database
                db.save_stock_data(stock_data)

                # Fetch and analyze news for selected stocks (if enabled)
                if enable_news:
                    for symbol in selected_stocks[:
                                                  5]:  # Analyze up to 5 stocks
                        try:
                            # Generate realistic news articles
                            articles = news_simulator.generate_news_articles(
                                symbol, 2)

                            # Analyze sentiment for each article
                            for article in articles:
                                sentiment_result = news_simulator.get_sentiment_for_content(
                                    f"{article['title']} {article['content']}")

                                # Save to database
                                db.save_news_article(
                                    symbol=symbol,
                                    title=article['title'],
                                    content=article['content'],
                                    url=article['url'],
                                    source=article['source'],
                                    published_date=article['published_date'],
                                    sentiment_score=sentiment_result['rating'],
                                    sentiment_confidence=sentiment_result[
                                        'confidence'])

                            # Update sentiment summary
                            db.update_sentiment_summary(symbol)

                        except Exception as e:
                            st.warning(
                                f"News analysis error for {symbol}: {str(e)}")
            except Exception as e:
                st.error(f"Error fetching stock data: {str(e)}")
                return

    stock_data = st.session_state.stock_data

    if not stock_data:
        st.error("No stock data available. Please try refreshing.")
        return

    # Display last update time
    if st.session_state.last_update:
        update_time = time.strftime(
            "%H:%M:%S", time.localtime(st.session_state.last_update))
        st.caption(f"Last updated: {update_time}")

    # Get sentiment data for all stocks
    sentiment_data = {}
    for symbol in stock_data.keys():
        sentiment_data[symbol] = db.get_sentiment_summary(symbol)

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
            header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns(
                [1, 1, 1, 1, 0.8])
            with header_col1:
                st.markdown("**Symbol**")
            with header_col2:
                st.markdown("**Price**")
            with header_col3:
                st.markdown("**Change $**")
            with header_col4:
                st.markdown("**Change %**")
            with header_col5:
                st.markdown("**Sentiment**")

            st.markdown("---")

            for symbol, data in sorted(up_stocks.items(),
                                       key=lambda x: x[1]['percent_change'],
                                       reverse=True):
                display_stock_card(symbol, data, sentiment_data.get(symbol))
        else:
            st.info("No stocks are up at the moment.")

    with col2:
        st.subheader("📉 Stocks Down")
        if down_stocks:
            # Add column headers
            header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns(
                [1, 1, 1, 1, 0.8])
            with header_col1:
                st.markdown("**Symbol**")
            with header_col2:
                st.markdown("**Price**")
            with header_col3:
                st.markdown("**Change $**")
            with header_col4:
                st.markdown("**Change %**")
            with header_col5:
                st.markdown("**Sentiment**")

            st.markdown("---")

            for symbol, data in sorted(down_stocks.items(),
                                       key=lambda x: x[1]['percent_change']):
                display_stock_card(symbol, data, sentiment_data.get(symbol))
        else:
            st.info("No stocks are down at the moment.")

    # Compact summary statistics
    total_stocks = len(stock_data)
    up_count = len(up_stocks)
    down_count = len(down_stocks)

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total", total_stocks)

    with col2:
        st.metric("Up", up_count)

    with col3:
        st.metric("Down", down_count)

    # Options Analysis Section
    if enable_options:
        st.markdown("---")
        st.markdown("## 📊 Cash Secured Put (CSP) Analysis")

        # Analyze options for selected stocks
        options_df = options_analyzer.get_top_csp_opportunities(
            selected_stocks, limit=15)
        options_analyzer.display_csp_summary(options_df)

    # Covered Call Analysis Section
    if enable_cc:
        st.markdown("---")
        st.markdown("## 🟦 Covered Call Analysis")

        # Analyze only specific stocks for covered calls
        cc_target_stocks = ['AAPL', 'AMZN', 'GOOGL', 'HOOD', 'NVDA', 'ORCL']
        cc_stocks_to_analyze = [s for s in cc_target_stocks if s in selected_stocks]
        
        if cc_stocks_to_analyze:
            cc_df = options_analyzer.get_top_cc_opportunities(
                cc_stocks_to_analyze, limit=15)
            options_analyzer.display_cc_summary(cc_df)
        else:
            st.info(f"Please select at least one of these stocks for Covered Call analysis: {', '.join(cc_target_stocks)}")

    # Portfolio Optimization Section
    if enable_portfolio_optimization:
        st.markdown("---")
        st.markdown("## 🎯 Portfolio Optimization")

        # Define target symbols for optimization
        target_symbols = ['AMZN', 'AAPL', 'GOOGL', 'HOOD']

        # Check if target symbols are available
        missing_symbols = [
            sym for sym in target_symbols if sym not in selected_stocks
        ]
        if missing_symbols:
            st.warning(
                f"Adding required symbols for optimization: {', '.join(missing_symbols)}"
            )
            # Add missing symbols temporarily for optimization
            optimization_symbols = target_symbols
        else:
            optimization_symbols = target_symbols

        # Run portfolio optimization
        portfolio_optimizer.display_portfolio_optimization(
            optimization_symbols)

    # Auto-refresh mechanism
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent excessive refreshing
        st.rerun()


if __name__ == "__main__":
    main()
