import pandas as pd
import requests

def fetch_robinhood_options(symbol):
    # Mock response for demonstration
    # Replace with actual API endpoint and authentication
    robinhood_url = f'https://mock-api.robinhood.com/options/?symbol={symbol}'
    
    # Uncomment below for actual API call
    # response = requests.get(robinhood_url)
    # data = response.json()
    
    # Simulated data for demonstration
    data = {
        'results': [
            {'type': 'call', 'premium': 2.5, 'symbol': symbol},
            {'type': 'put', 'premium': 1.5, 'symbol': symbol}
        ]
    }
    
    premiums = [{'Type': option['type'], 'Premium': option['premium'], 'Symbol': option['symbol']} for option in data['results']]
    return premiums

def fetch_merrill_edge_options(symbol):
    # Mock response for demonstration
    # Replace with actual API endpoint and authentication
    merrill_edge_url = f'https://mock-api.ml.com/options/?symbol={symbol}'
    
    # Uncomment below for actual API call
    # response = requests.get(merrill_edge_url)
    # data = response.json()
    
    # Simulated data for demonstration
    data = {
        'results': [
            {'type': 'call', 'premium': 3.0, 'symbol': symbol},
            {'type': 'put', 'premium': 2.0, 'symbol': symbol}
        ]
    }
    
    premiums = [{'Type': option['type'], 'Premium': option['premium'], 'Symbol': option['symbol']} for option in data['results']]
    return premiums

def main():
    symbols = ['AAPL', 'TSLA']  # Add your stocks here
    all_options = []

    for symbol in symbols:
        robinhood_data = fetch_robinhood_options(symbol)
        merrill_edge_data = fetch_merrill_edge_options(symbol)
        
        all_options.extend(robinhood_data)
        all_options.extend(merrill_edge_data)
        
    # Creating a DataFrame and saving to CSV
    df = pd.DataFrame(all_options)
    df.to_csv('option_premiums.csv', index=False)
    print("Data saved to option_premiums.csv")

if __name__ == "__main__":
    main()
