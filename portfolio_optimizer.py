import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import streamlit as st
from options_analyzer import OptionsAnalyzer
from itertools import product
import math

class PortfolioOptimizer:
    """Optimize portfolio allocation for CSP options across multiple stocks"""
    
    def __init__(self, total_capital: float = 100000):
        self.total_capital = total_capital
        self.options_analyzer = OptionsAnalyzer()
        self.min_allocation_per_stock = 0.15  # Minimum 15% per stock
        self.max_allocation_per_stock = 0.60  # Maximum 60% per stock
    
    def get_common_expiry_options(self, symbols: List[str]) -> Dict[str, Dict[str, List[Dict]]]:
        """Get CSP options for all symbols grouped by common expiry dates"""
        all_options = {}
        
        for symbol in symbols:
            options = self.options_analyzer.analyze_csp_options(symbol)
            if options:
                all_options[symbol] = {}
                for option in options:
                    expiry = option['expiration']
                    if expiry not in all_options[symbol]:
                        all_options[symbol][expiry] = []
                    all_options[symbol][expiry].append(option)
        
        return all_options
    
    def find_common_expiry_dates(self, options_data: Dict[str, Dict[str, List[Dict]]]) -> List[str]:
        """Find expiry dates that are common across all symbols"""
        if not options_data:
            return []
        
        # Get expiry dates for each symbol
        symbol_expiries = []
        for symbol, expiry_dict in options_data.items():
            symbol_expiries.append(set(expiry_dict.keys()))
        
        # Find intersection of all sets
        common_expiries = symbol_expiries[0]
        for expiry_set in symbol_expiries[1:]:
            common_expiries = common_expiries.intersection(expiry_set)
        
        return sorted(list(common_expiries))
    
    def calculate_contracts_and_allocation(self, option: Dict[str, Any], allocated_capital: float) -> Tuple[int, float, float]:
        """Calculate number of contracts and actual allocation for given capital"""
        collateral_per_contract = option['strike'] * 100
        max_contracts = int(allocated_capital / collateral_per_contract)
        actual_allocation = max_contracts * collateral_per_contract
        total_premium = max_contracts * option['premium'] * 100
        
        return max_contracts, actual_allocation, total_premium
    
    def optimize_allocation_for_expiry(self, symbols: List[str], expiry_date: str, 
                                     options_data: Dict[str, Dict[str, List[Dict]]]) -> Dict[str, Any]:
        """Optimize allocation for a specific expiry date with maximum capital utilization"""
        
        # Get options for this expiry date for all symbols
        expiry_options = {}
        for symbol in symbols:
            if symbol in options_data and expiry_date in options_data[symbol]:
                expiry_options[symbol] = options_data[symbol][expiry_date]
            else:
                return None  # Cannot optimize if any symbol missing options
        
        best_allocation = None
        best_score = 0  # Combined score: premium percentage + capital utilization
        
        # Get top options for each symbol
        symbol_best_options = {}
        for symbol in symbols:
            sorted_options = sorted(expiry_options[symbol], 
                                  key=lambda x: x['premium_percentage'], 
                                  reverse=True)
            symbol_best_options[symbol] = sorted_options[:5]  # Top 5 options per symbol
        
        # Test combinations of options
        option_combinations = product(*[symbol_best_options[symbol] for symbol in symbols])
        
        for option_combo in option_combinations:
            # Use iterative allocation to maximize capital utilization
            allocation_result = self._maximize_capital_utilization(symbols, option_combo)
            
            if allocation_result:
                # Calculate combined score: 70% premium percentage + 30% capital efficiency
                premium_score = allocation_result['total_premium_percentage']
                capital_score = allocation_result['capital_efficiency']
                combined_score = (premium_score * 0.7) + (capital_score * 0.3)
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_allocation = allocation_result
        
        if best_allocation:
            best_allocation['expiry_date'] = expiry_date
            best_allocation['days_to_expiry'] = best_allocation['allocations'][0]['days_to_exp']
        
        return best_allocation
    
    def _test_allocation(self, symbols: List[str], allocation_percentages: Tuple[float], 
                        option_combo: Tuple[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Test a specific allocation combination"""
        
        allocations = []
        total_allocated_capital = 0
        total_premium = 0
        
        for i, symbol in enumerate(symbols):
            option = option_combo[i]
            allocated_capital = self.total_capital * allocation_percentages[i]
            
            contracts, actual_allocation, premium = self.calculate_contracts_and_allocation(
                option, allocated_capital
            )
            
            if contracts == 0:  # Cannot allocate any contracts
                return None
            
            allocations.append({
                'symbol': symbol,
                'option': option,
                'allocated_capital': allocated_capital,
                'actual_allocation': actual_allocation,
                'contracts': contracts,
                'premium': premium,
                'premium_percentage': option['premium_percentage'],
                'strike': option['strike'],
                'delta': option['delta'],
                'days_to_exp': option['days_to_exp'],
                'breakeven': option['breakeven']
            })
            
            total_allocated_capital += actual_allocation
            total_premium += premium
        
        # Calculate overall metrics
        total_premium_percentage = (total_premium / total_allocated_capital) * 100 if total_allocated_capital > 0 else 0
        unused_capital = self.total_capital - total_allocated_capital
        
        return {
            'allocations': allocations,
            'total_allocated_capital': total_allocated_capital,
            'total_premium': total_premium,
            'total_premium_percentage': total_premium_percentage,
            'unused_capital': unused_capital,
            'capital_efficiency': (total_allocated_capital / self.total_capital) * 100
        }
    
    def _maximize_capital_utilization(self, symbols: List[str], option_combo: Tuple[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Maximize capital utilization using iterative allocation"""
        
        # Start with minimum allocation for each stock
        min_capital_per_stock = self.total_capital * self.min_allocation_per_stock
        allocations = []
        remaining_capital = self.total_capital
        
        # First pass: ensure minimum allocation for each stock
        for i, symbol in enumerate(symbols):
            option = option_combo[i]
            collateral_per_contract = option['strike'] * 100
            
            # Calculate minimum contracts needed
            min_contracts = max(1, int(min_capital_per_stock / collateral_per_contract))
            min_allocation = min_contracts * collateral_per_contract
            
            if min_allocation > remaining_capital:
                return None  # Cannot satisfy minimum requirements
            
            contracts, actual_allocation, premium = self.calculate_contracts_and_allocation(
                option, min_allocation
            )
            
            if contracts == 0:
                return None
            
            allocations.append({
                'symbol': symbol,
                'option': option,
                'allocated_capital': min_allocation,
                'actual_allocation': actual_allocation,
                'contracts': contracts,
                'premium': premium,
                'premium_percentage': option['premium_percentage'],
                'strike': option['strike'],
                'delta': option['delta'],
                'days_to_exp': option['days_to_exp'],
                'breakeven': option['breakeven']
            })
            
            remaining_capital -= actual_allocation
        
        # Second pass: distribute remaining capital to maximize premium
        # Continue until unused capital cannot buy another contract for ANY stock
        while True:
            best_addition = None
            best_premium_gain = 0
            best_idx = -1
            
            # Find the best stock to add another contract
            for i, alloc in enumerate(allocations):
                option = alloc['option']
                collateral_per_contract = option['strike'] * 100
                
                # Check if we can add another contract
                if (collateral_per_contract <= remaining_capital and 
                    alloc['actual_allocation'] + collateral_per_contract <= self.total_capital * self.max_allocation_per_stock):
                    
                    # Calculate premium gain per dollar
                    premium_gain = option['premium'] * 100
                    premium_gain_ratio = premium_gain / collateral_per_contract
                    
                    if premium_gain_ratio > best_premium_gain:
                        best_premium_gain = premium_gain_ratio
                        best_addition = collateral_per_contract
                        best_idx = i
            
            # Add the best contract if found
            if best_idx >= 0 and best_addition:
                allocations[best_idx]['contracts'] += 1
                allocations[best_idx]['actual_allocation'] += best_addition
                allocations[best_idx]['premium'] += allocations[best_idx]['option']['premium'] * 100
                remaining_capital -= best_addition
            else:
                break  # No more beneficial additions possible
        
        # Verify that unused capital cannot buy any contract
        min_contract_cost = min(alloc['option']['strike'] * 100 for alloc in allocations)
        if remaining_capital >= min_contract_cost:
            # This shouldn't happen with proper optimization, but let's handle it
            # Try one more round of allocation to any stock that can accept it
            for alloc in allocations:
                collateral_per_contract = alloc['option']['strike'] * 100
                if (collateral_per_contract <= remaining_capital and 
                    alloc['actual_allocation'] + collateral_per_contract <= self.total_capital * self.max_allocation_per_stock):
                    alloc['contracts'] += 1
                    alloc['actual_allocation'] += collateral_per_contract
                    alloc['premium'] += alloc['option']['premium'] * 100
                    remaining_capital -= collateral_per_contract
                    break
        
        # Calculate final metrics
        total_allocated_capital = sum(alloc['actual_allocation'] for alloc in allocations)
        total_premium = sum(alloc['premium'] for alloc in allocations)
        total_premium_percentage = (total_premium / total_allocated_capital) * 100 if total_allocated_capital > 0 else 0
        unused_capital = self.total_capital - total_allocated_capital
        
        return {
            'allocations': allocations,
            'total_allocated_capital': total_allocated_capital,
            'total_premium': total_premium,
            'total_premium_percentage': total_premium_percentage,
            'unused_capital': unused_capital,
            'capital_efficiency': (total_allocated_capital / self.total_capital) * 100
        }
    
    def optimize_portfolio(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Optimize portfolio across all common expiry dates"""
        
        # Get all options data
        with st.spinner("Analyzing options for portfolio optimization..."):
            options_data = self.get_common_expiry_options(symbols)
        
        if not options_data:
            return []
        
        # Find common expiry dates
        common_expiries = self.find_common_expiry_dates(options_data)
        
        if not common_expiries:
            return []
        
        # Optimize for each common expiry date
        optimized_portfolios = []
        
        for expiry in common_expiries:
            with st.spinner(f"Optimizing allocation for {expiry}..."):
                result = self.optimize_allocation_for_expiry(symbols, expiry, options_data)
                if result:
                    optimized_portfolios.append(result)
        
        # Sort by total premium percentage
        optimized_portfolios.sort(key=lambda x: x['total_premium_percentage'], reverse=True)
        
        return optimized_portfolios
    
    def display_portfolio_optimization(self, symbols: List[str]) -> None:
        """Display portfolio optimization results in Streamlit"""
        
        st.subheader(f"💰 Portfolio Optimization: ${self.total_capital:,.0f}")
        st.caption(f"Optimizing allocation across {', '.join(symbols)} with same expiry dates")
        
        # Get optimized portfolios
        portfolios = self.optimize_portfolio(symbols)
        
        if not portfolios:
            st.warning("No common expiry dates found for all selected stocks with suitable CSP options")
            return
        
        # Display summary metrics for best portfolio
        best_portfolio = portfolios[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Best Premium %", f"{best_portfolio['total_premium_percentage']:.2f}%")
        
        with col2:
            st.metric("Total Premium", f"${best_portfolio['total_premium']:,.0f}")
        
        with col3:
            st.metric("Capital Used", f"${best_portfolio['total_allocated_capital']:,.0f}")
        
        with col4:
            unused_capital = best_portfolio['unused_capital']
            min_contract_cost = min(alloc['option']['strike'] * 100 for alloc in best_portfolio['allocations'])
            if unused_capital < min_contract_cost:
                st.metric("Capital Status", "✓ Fully Utilized", delta=f"${unused_capital:,.0f} unused")
            else:
                st.metric("Capital Status", "⚠ Can Add More", delta=f"${unused_capital:,.0f} unused")
        
        # Display top portfolio options
        st.markdown("### 🎯 Top Portfolio Allocations")
        
        for i, portfolio in enumerate(portfolios[:3]):  # Show top 3
            with st.expander(f"Option {i+1}: {portfolio['expiry_date']} ({portfolio['days_to_expiry']} days) - {portfolio['total_premium_percentage']:.2f}% premium"):
                
                # Create allocation table
                allocation_data = []
                for alloc in portfolio['allocations']:
                    allocation_data.append({
                        'Symbol': alloc['symbol'],
                        'Strike': f"${alloc['strike']:.2f}",
                        'Contracts': alloc['contracts'],
                        'Capital Used': f"${alloc['actual_allocation']:,.0f}",
                        'Premium': f"${alloc['premium']:,.0f}",
                        'Premium %': f"{alloc['premium_percentage']:.2f}%",
                        'Delta': f"{alloc['delta']:.3f}",
                        'Breakeven': f"${alloc['breakeven']:.2f}"
                    })
                
                df = pd.DataFrame(allocation_data)
                st.dataframe(df, use_container_width=True)
                
                # Summary for this portfolio
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Capital Used", f"${portfolio['total_allocated_capital']:,.0f}")
                with col2:
                    unused_capital = portfolio['unused_capital']
                    min_contract_cost = min(alloc['option']['strike'] * 100 for alloc in portfolio['allocations'])
                    if unused_capital < min_contract_cost:
                        st.metric("Unused Capital", f"${unused_capital:,.0f}", delta="✓ Cannot buy more contracts")
                    else:
                        st.metric("Unused Capital", f"${unused_capital:,.0f}", delta="⚠ Can buy more contracts")
                with col3:
                    annualized_return = (portfolio['total_premium_percentage'] * 365) / portfolio['days_to_expiry']
                    st.metric("Annualized Return", f"{annualized_return:.1f}%")
        
        # Risk disclaimer
        st.markdown("---")
        st.caption("⚠️ **Risk Disclaimer**: This optimization assumes maximum capital allocation to CSP strategies. Each position requires sufficient capital to purchase 100 shares per contract at strike price. Consider diversification and risk management in your actual trading strategy.")
        
        # Export functionality
        if portfolios:
            st.markdown("### 📊 Export Data")
            if st.button("Generate Detailed Report"):
                self._generate_detailed_report(portfolios[:3])
    
    def _generate_detailed_report(self, portfolios: List[Dict[str, Any]]) -> None:
        """Generate a detailed report of portfolio allocations"""
        
        report_data = []
        
        for i, portfolio in enumerate(portfolios):
            for alloc in portfolio['allocations']:
                report_data.append({
                    'Portfolio_Rank': i + 1,
                    'Expiry_Date': portfolio['expiry_date'],
                    'Days_To_Expiry': portfolio['days_to_expiry'],
                    'Symbol': alloc['symbol'],
                    'Strike_Price': alloc['strike'],
                    'Current_Price': alloc['option']['current_price'],
                    'Contracts': alloc['contracts'],
                    'Capital_Allocated': alloc['actual_allocation'],
                    'Premium_Collected': alloc['premium'],
                    'Premium_Percentage': alloc['premium_percentage'],
                    'Delta': alloc['delta'],
                    'Breakeven_Price': alloc['breakeven'],
                    'Max_Loss_Per_Contract': (alloc['strike'] - alloc['option']['current_price']) * 100,
                    'Portfolio_Premium_Total': portfolio['total_premium'],
                    'Portfolio_Premium_Percentage': portfolio['total_premium_percentage']
                })
        
        df_report = pd.DataFrame(report_data)
        
        st.markdown("#### Detailed Portfolio Report")
        st.dataframe(df_report, use_container_width=True)
        
        # Download link
        csv = df_report.to_csv(index=False)
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name=f"csp_portfolio_optimization_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )