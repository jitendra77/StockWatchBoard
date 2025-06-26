# Stock Dashboard Application

## Overview

This is a comprehensive Streamlit-based stock dashboard application that provides real-time stock data, news sentiment analysis, and Cash Secured Put (CSP) options analysis. The application displays stocks in a two-column layout segregated by performance (up vs down), with integrated sentiment scoring and options trading opportunities.

## System Architecture

The application follows a modular architecture with separate components for different functionalities:

- **Frontend**: Streamlit web interface for user interaction and data visualization
- **Data Layer**: Google Cloud BigQuery integration for persistent storage of stock data, news, and sentiment analysis
- **External APIs**: Yahoo Finance for stock data, yfinance for options data
- **Business Logic**: Modular classes for stock fetching, news processing, sentiment analysis, and options analysis

## Key Components

### 1. Frontend (app.py)
- **Technology**: Streamlit web framework
- **Purpose**: Provides the main user interface with real-time dashboard functionality
- **Features**: 
  - Auto-refresh capabilities
  - Two-column layout for up/down stock segregation
  - Currency formatting and change indicators
  - Color-coded positive/negative changes
  - Options analysis toggle for CSP strategies

### 2. Database Management (database.py)
- **Technology**: Google Cloud BigQuery
- **Purpose**: Handles persistent storage of stock data, news articles, and sentiment scores
- **Authentication**: Multiple methods including service account JSON file, environment variables, and default credentials
- **Tables**: Manages creation and interaction with stock-related tables in BigQuery

### 3. Stock Data Fetching (stock_fetcher.py)
- **Technology**: yfinance library
- **Purpose**: Retrieves real-time and historical stock data
- **Features**:
  - Current price fetching
  - Historical data for change calculations
  - Error handling for missing data
  - Caching mechanisms (30-second duration)

### 4. News Processing (news_simulator.py)
- **Technology**: Template-based realistic news generation
- **Purpose**: Generates realistic news articles with varied sentiment for demonstration
- **Features**:
  - Company-specific news templates
  - Sentiment-based content generation
  - Randomized but realistic publishing dates
  - Multiple news source simulation

### 5. Sentiment Analysis (sentiment_analyzer.py)
- **Technology**: Keyword-based sentiment analysis with OpenAI fallback
- **Purpose**: Analyzes sentiment of news articles and provides 1-5 star ratings
- **Algorithm**: 
  - Uses predefined positive and negative word dictionaries
  - Calculates sentiment scores on 1-5 scale
  - Provides confidence ratings
  - OpenAI integration available with API key

### 6. Options Analysis (options_analyzer.py)
- **Technology**: yfinance options data with Black-Scholes delta calculations
- **Purpose**: Identifies Cash Secured Put opportunities with specific criteria
- **Features**:
  - Delta range filtering (0.17-0.23)
  - Expiration filtering (within 7 days)
  - Premium percentage calculations
  - Annualized return projections
  - Collateral requirements
  - Risk metrics and breakeven analysis

### 7. Portfolio Optimization (portfolio_optimizer.py)
- **Technology**: Advanced allocation algorithms with constraint optimization
- **Purpose**: Optimizes $100k capital allocation across AMZN, AAPL, GOOGL with same expiry
- **Features**:
  - Common expiry date identification across all three stocks
  - Allocation constraint enforcement (15-60% per stock)
  - Premium percentage maximization algorithms
  - Capital efficiency calculations
  - Multiple allocation scenario testing
  - Detailed reporting and CSV export functionality

## Data Flow

1. **Stock Data Collection**: StockFetcher retrieves data from Yahoo Finance API
2. **News Generation**: NewsSimulator creates realistic articles with sentiment bias
3. **Sentiment Processing**: SentimentAnalyzer evaluates news content for market sentiment
4. **Options Analysis**: OptionsAnalyzer identifies CSP opportunities based on delta and expiration criteria
5. **Data Storage**: DatabaseManager stores all processed data in BigQuery
6. **Frontend Display**: Streamlit app retrieves and displays data with real-time updates

## External Dependencies

### Core Libraries
- **streamlit**: Web framework for the dashboard interface
- **yfinance**: Stock and options data retrieval from Yahoo Finance
- **google-cloud-bigquery**: Cloud database integration
- **pandas/numpy**: Data manipulation and analysis
- **scipy**: Statistical functions for Black-Scholes calculations
- **requests/beautifulsoup4**: Web scraping capabilities (fallback)
- **trafilatura**: Content extraction from web pages

### Authentication
- Google Cloud service account credentials required for BigQuery access
- Multiple authentication methods supported for flexibility

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with comprehensive package environment
- **Port**: Application runs on port 5000, exposed as port 80
- **Deployment**: Autoscale deployment target for production
- **Workflow**: Parallel execution with dedicated Streamlit server task

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON file
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Direct JSON credentials string (backup)
- `GOOGLE_CLOUD_PROJECT_ID`: Google Cloud project identifier

### Configuration
- Streamlit configured for headless operation
- Server address set to 0.0.0.0 for container compatibility
- Light theme default for better readability

## Recent Changes

### June 26, 2025
- Fixed news articles and sentiment scores not populating by implementing NewsSimulator
- Updated default stocks to show 8 companies instead of 6
- Expanded stock selection to 30 popular symbols across multiple sectors
- Added comprehensive Cash Secured Put (CSP) options analysis
- Integrated Black-Scholes delta calculations for options filtering
- Added premium percentage calculations relative to collateral required
- Implemented expiration date filtering for options within next week
- Created detailed options analysis table with risk metrics
- Enhanced BigQuery authentication to handle file-based credentials
- Improved error handling for JSON credential truncation issues
- **Added Portfolio Optimization Engine**: Optimizes $100k allocation across AMZN, AAPL, GOOGL
- **Implemented allocation constraints**: 15-60% per stock with 5% increment testing
- **Added common expiry date filtering**: Ensures all three stocks have options on same date
- **Created comprehensive optimization metrics**: Premium percentage, capital efficiency, annualized returns
- **Built detailed reporting system**: CSV export and allocation breakdown tables

## User Preferences

- Preferred communication style: Simple, everyday language
- Default display: 8 stocks showing in two-column up/down layout
- News analysis: Enabled by default with realistic sentiment data
- Options analysis: Available as optional feature for CSP strategies
- Refresh frequency: 30-second cache with manual refresh capability