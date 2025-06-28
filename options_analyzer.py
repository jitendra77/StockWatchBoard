import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional
import streamlit as st
from scipy.stats import norm
import math

class OptionsAnalyzer:
    """Analyze options data for Cash Secured Put strategies"""
    
    def __init__(self):
        self.risk_free_rate = 0.05  # 5% risk-free rate assumption
    
    def calculate_black_scholes_delta(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = 'put') -> float:
        """Calculate Black-Scholes delta for options"""
        try:
            if T <= 0 or sigma <= 0:
                return 0.0
            
            d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
            
            if option_type.lower() == 'put':
                delta = -norm.cdf(-d1)
            else:  # call
                delta = norm.cdf(d1)
            
            return delta
        except:
            return 0.0
    
    def get_implied_volatility_estimate(self, symbol: str) -> float:
        """Estimate implied volatility from historical data"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="30d")
            if len(hist) < 2:
                return 0.25  # Default 25% volatility
            
            returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            return max(0.1, min(2.0, volatility))  # Cap between 10% and 200%
        except:
            return 0.25
    
    def get_options_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch options data for a stock symbol"""
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            
            # Get options expiration dates
            expiration_dates = stock.options
            if not expiration_dates:
                return None
            
            # Filter for next week (within 10 days)
            today = datetime.now().date()
            next_week = today + timedelta(days=10)
            
            valid_expirations = []
            for exp_str in expiration_dates:
                exp_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
                if today < exp_date <= next_week:
                    valid_expirations.append(exp_str)
            
            if not valid_expirations:
                return None
            
            # Get implied volatility estimate
            iv = self.get_implied_volatility_estimate(symbol)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'expiration_dates': valid_expirations,
                'implied_volatility': iv
            }
            
        except Exception as e:
            return None
    
    def analyze_csp_options(self, symbol: str) -> List[Dict[str, Any]]:
        """Analyze Cash Secured Put options for a symbol"""
        options_data = self.get_options_data(symbol)
        if not options_data:
            return []
        
        current_price = options_data['current_price']
        iv = options_data['implied_volatility']
        csp_opportunities = []
        
        for exp_date in options_data['expiration_dates']:
            try:
                stock = yf.Ticker(symbol)
                option_chain = stock.option_chain(exp_date)
                puts = option_chain.puts
                
                if puts.empty:
                    continue
                
                # Calculate time to expiration
                exp_datetime = datetime.strptime(exp_date, '%Y-%m-%d')
                days_to_exp = (exp_datetime.date() - datetime.now().date()).days
                time_to_exp = days_to_exp / 365.0
                
                for _, put in puts.iterrows():
                    strike = put['strike']
                    bid = put['bid']
                    ask = put['ask']
                    
                    # Skip if no meaningful bid/ask
                    if bid <= 0 or ask <= 0:
                        continue
                    
                    # Calculate mid-price premium
                    premium = (bid + ask) / 2
                    
                    # Calculate delta using Black-Scholes
                    delta = self.calculate_black_scholes_delta(
                        S=current_price,
                        K=strike,
                        T=time_to_exp,
                        r=self.risk_free_rate,
                        sigma=iv,
                        option_type='put'
                    )
                    
                    # Filter for delta range 0.15 to 0.25 (absolute value)
                    abs_delta = abs(delta)
                    if 0.15 <= abs_delta <= 0.25:
                        # Calculate premium as percentage of collateral (strike price)
                        premium_percentage = (premium / strike) * 100
                        
                        # Calculate annualized return
                        if days_to_exp > 0:
                            annualized_return = (premium_percentage * 365) / days_to_exp
                        else:
                            annualized_return = 0
                        
                        csp_opportunities.append({
                            'symbol': symbol,
                            'expiration': exp_date,
                            'days_to_exp': days_to_exp,
                            'strike': strike,
                            'current_price': current_price,
                            'bid': bid,
                            'ask': ask,
                            'premium': premium,
                            'delta': delta,
                            'abs_delta': abs_delta,
                            'premium_percentage': premium_percentage,
                            'annualized_return': annualized_return,
                            'collateral_required': strike * 100,  # Per contract
                            'max_profit': premium * 100,  # Per contract
                            'breakeven': strike - premium
                        })
                        
            except Exception as e:
                continue
        
        # Sort by premium percentage (highest first)
        csp_opportunities.sort(key=lambda x: x['premium_percentage'], reverse=True)
        return csp_opportunities
    
    def analyze_multiple_stocks(self, symbols: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze CSP opportunities for multiple stocks"""
        all_opportunities = {}
        
        for symbol in symbols:
            with st.spinner(f"Analyzing options for {symbol}..."):
                opportunities = self.analyze_csp_options(symbol)
                if opportunities:
                    all_opportunities[symbol] = opportunities
        
        return all_opportunities
    
    def create_opportunities_dataframe(self, opportunities: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """Create a DataFrame from CSP opportunities"""
        all_data = []
        
        for symbol, symbol_opportunities in opportunities.items():
            all_data.extend(symbol_opportunities)
        
        if not all_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        
        # Round numerical columns for display
        numerical_columns = ['premium', 'delta', 'abs_delta', 'premium_percentage', 
                           'annualized_return', 'collateral_required', 'max_profit']
        
        for col in numerical_columns:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    
    def get_top_csp_opportunities(self, symbols: List[str], limit: int = 10) -> pd.DataFrame:
        """Get top CSP opportunities across all symbols"""
        opportunities = self.analyze_multiple_stocks(symbols)
        df = self.create_opportunities_dataframe(opportunities)
        
        if df.empty:
            return df
        
        # Sort by premium percentage and return top opportunities
        df_sorted = df.sort_values('premium_percentage', ascending=False)
        return df_sorted.head(limit)
    
    def display_csp_summary(self, df: pd.DataFrame) -> None:
        """Display CSP opportunities in Streamlit"""
        if df.empty:
            st.warning("No CSP opportunities found with delta range 0.15-0.25 expiring within next week")
            return
        
        st.subheader("🎯 Cash Secured Put Opportunities")
        st.caption("Put options with delta between 0.15-0.25 expiring within 10 days")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Opportunities", len(df))
        
        with col2:
            avg_premium = df['premium_percentage'].mean()
            st.metric("Avg Premium %", f"{avg_premium:.2f}%")
        
        with col3:
            avg_annual = df['annualized_return'].mean()
            st.metric("Avg Annualized Return", f"{avg_annual:.1f}%")
        
        with col4:
            unique_stocks = df['symbol'].nunique()
            st.metric("Stocks Analyzed", unique_stocks)
        
        # Display detailed table
        display_columns = [
            'symbol', 'expiration', 'days_to_exp', 'strike', 'current_price',
            'premium', 'abs_delta', 'premium_percentage', 'annualized_return',
            'breakeven'
        ]
        
        display_df = df[display_columns].copy()
        display_df.columns = [
            'Symbol', 'Expiration', 'Days', 'Strike', 'Current Price',
            'Premium', 'Delta', 'Premium %', 'Annual Return %', 'Breakeven'
        ]
        
        # Format the dataframe for better display
        display_df['Premium %'] = display_df['Premium %'].apply(lambda x: f"{x:.2f}%")
        display_df['Annual Return %'] = display_df['Annual Return %'].apply(lambda x: f"{x:.1f}%")
        display_df['Delta'] = display_df['Delta'].apply(lambda x: f"{x:.3f}")
        display_df['Premium'] = display_df['Premium'].apply(lambda x: f"${x:.2f}")
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"${x:.2f}")
        display_df['Breakeven'] = display_df['Breakeven'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(display_df, use_container_width=True)
        
        # Risk disclaimer
        st.caption("⚠️ **Risk Disclaimer**: Options trading involves significant risk. CSP requires sufficient capital to purchase 100 shares at strike price. Past performance does not guarantee future results.")