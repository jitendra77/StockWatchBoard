import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import streamlit as st

class StockFetcher:
    """Class to handle stock data fetching and processing"""
    
    def __init__(self):
        self.cache_duration = 300  # Cache duration in seconds
    
    def fetch_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch stock information for a single symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Dictionary containing stock data
        """
        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get current info
            info = ticker.info
            
            # Get historical data for the last 2 days to calculate change
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) < 2:
                # If we can't get historical data, try to get current price from info
                current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                previous_close = info.get('previousClose', current_price)
            else:
                # Use the most recent price
                current_price = hist['Close'].iloc[-1]
                previous_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
            
            # Calculate changes
            change = current_price - previous_close
            percent_change = (change / previous_close * 100) if previous_close != 0 else 0
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'previous_close': float(previous_close),
                'change': float(change),
                'percent_change': float(percent_change),
                'volume': info.get('volume', 0),
                'market_cap': info.get('marketCap', 0),
                'company_name': info.get('longName', symbol)
            }
            
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {str(e)}")
            # Return default data structure with zeros
            return {
                'symbol': symbol,
                'current_price': 0.0,
                'previous_close': 0.0,
                'change': 0.0,
                'percent_change': 0.0,
                'volume': 0,
                'market_cap': 0,
                'company_name': symbol,
                'error': str(e)
            }
    
    def fetch_stocks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch stock data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary with symbol as key and stock data as value
        """
        stock_data = {}
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_symbols = len(symbols)
        
        for i, symbol in enumerate(symbols):
            # Update progress
            progress = (i + 1) / total_symbols
            progress_bar.progress(progress)
            status_text.text(f"Fetching {symbol}... ({i + 1}/{total_symbols})")
            
            # Fetch data for the symbol
            data = self.fetch_stock_info(symbol)
            
            # Only include if we got valid data
            if data['current_price'] > 0:
                stock_data[symbol] = data
            else:
                st.warning(f"Skipped {symbol}: Invalid or missing data")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        if not stock_data:
            raise Exception("No valid stock data could be fetched. Please check your internet connection and try again.")
        
        return stock_data
    
    def get_market_summary(self, stock_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate market summary statistics
        
        Args:
            stock_data: Dictionary of stock data
            
        Returns:
            Summary statistics
        """
        if not stock_data:
            return {}
        
        changes = [data['percent_change'] for data in stock_data.values()]
        
        return {
            'total_stocks': len(stock_data),
            'stocks_up': len([c for c in changes if c > 0]),
            'stocks_down': len([c for c in changes if c < 0]),
            'stocks_unchanged': len([c for c in changes if c == 0]),
            'avg_change': np.mean(changes),
            'max_gainer': max(changes) if changes else 0,
            'max_loser': min(changes) if changes else 0
        }
