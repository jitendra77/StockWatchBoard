from google.cloud import bigquery
from google.oauth2 import service_account
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st

class DatabaseManager:
    """BigQuery database manager for stock data, news, and sentiment analysis"""
    
    def __init__(self):
        self.project_id = None
        self.dataset_id = "stock_dashboard"
        self.client = None
        self.init_bigquery_client()
        self.init_tables()
    
    def init_bigquery_client(self):
        """Initialize BigQuery client with authentication"""
        try:
            # Method 1: Try file path
            credentials_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_file and os.path.exists(credentials_file):
                self.client = bigquery.Client.from_service_account_json(credentials_file)
                self.project_id = self.client.project
                st.success(f"Connected to BigQuery project: {self.project_id}")
                return
            
            # Method 2: Try JSON string from environment
            credentials_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT_ID')
            
            if credentials_json and project_id:
                credentials_info = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                self.client = bigquery.Client(credentials=credentials, project=project_id)
                self.project_id = project_id
                st.success(f"Connected to BigQuery project: {self.project_id}")
                return
            
            # Method 3: Try default authentication
            self.client = bigquery.Client()
            self.project_id = self.client.project
            st.success(f"Connected to BigQuery project: {self.project_id}")
            
        except Exception as e:
            st.error(f"BigQuery authentication failed: {str(e)}")
            st.info("Place your credentials.json file in the project directory and set GOOGLE_APPLICATION_CREDENTIALS=credentials.json")
            self.client = None
    
    def init_tables(self):
        """Initialize BigQuery dataset and tables"""
        if not self.client:
            return
            
        try:
            # Create dataset if it doesn't exist
            dataset_ref = self.client.dataset(self.dataset_id)
            try:
                self.client.get_dataset(dataset_ref)
            except:
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"
                self.client.create_dataset(dataset)
                st.info(f"Created dataset: {self.dataset_id}")
            
            # Create stock_data table
            stock_table_id = f"{self.project_id}.{self.dataset_id}.stock_data"
            stock_schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("current_price", "FLOAT64"),
                bigquery.SchemaField("previous_close", "FLOAT64"),
                bigquery.SchemaField("change_amount", "FLOAT64"),
                bigquery.SchemaField("change_percent", "FLOAT64"),
                bigquery.SchemaField("volume", "INT64"),
                bigquery.SchemaField("market_cap", "INT64"),
                bigquery.SchemaField("company_name", "STRING"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            try:
                self.client.get_table(stock_table_id)
            except:
                table = bigquery.Table(stock_table_id, schema=stock_schema)
                self.client.create_table(table)
                st.info("Created stock_data table")
            
            # Create news_articles table
            news_table_id = f"{self.project_id}.{self.dataset_id}.news_articles"
            news_schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("content", "STRING"),
                bigquery.SchemaField("url", "STRING"),
                bigquery.SchemaField("source", "STRING"),
                bigquery.SchemaField("published_date", "TIMESTAMP"),
                bigquery.SchemaField("sentiment_score", "FLOAT64"),
                bigquery.SchemaField("sentiment_confidence", "FLOAT64"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            try:
                self.client.get_table(news_table_id)
            except:
                table = bigquery.Table(news_table_id, schema=news_schema)
                self.client.create_table(table)
                st.info("Created news_articles table")
            
            # Create stock_sentiment table
            sentiment_table_id = f"{self.project_id}.{self.dataset_id}.stock_sentiment"
            sentiment_schema = [
                bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("avg_sentiment", "FLOAT64"),
                bigquery.SchemaField("total_articles", "INT64"),
                bigquery.SchemaField("positive_articles", "INT64"),
                bigquery.SchemaField("negative_articles", "INT64"),
                bigquery.SchemaField("neutral_articles", "INT64"),
                bigquery.SchemaField("calculated_date", "DATE"),
                bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            ]
            
            try:
                self.client.get_table(sentiment_table_id)
            except:
                table = bigquery.Table(sentiment_table_id, schema=sentiment_schema)
                self.client.create_table(table)
                st.info("Created stock_sentiment table")
                
        except Exception as e:
            st.error(f"BigQuery table initialization error: {str(e)}")
    
    def save_stock_data(self, stock_data: Dict[str, Dict[str, Any]]):
        """Save stock data to BigQuery"""
        if not self.client:
            return
            
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.stock_data"
            
            rows_to_insert = []
            current_time = datetime.now()
            
            for symbol, data in stock_data.items():
                row = {
                    "id": f"{symbol}_{int(current_time.timestamp())}",
                    "symbol": symbol,
                    "current_price": float(data.get('current_price', 0)),
                    "previous_close": float(data.get('previous_close', 0)),
                    "change_amount": float(data.get('change', 0)),
                    "change_percent": float(data.get('percent_change', 0)),
                    "volume": int(data.get('volume', 0)),
                    "market_cap": int(data.get('market_cap', 0)),
                    "company_name": data.get('company_name', symbol),
                    "timestamp": current_time.isoformat()
                }
                rows_to_insert.append(row)
            
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            if errors:
                st.warning(f"BigQuery insert errors: {errors}")
            
        except Exception as e:
            st.warning(f"Error saving stock data to BigQuery: {str(e)}")
    
    def save_news_article(self, symbol: str, title: str, content: str, 
                         url: str, source: str, published_date: datetime,
                         sentiment_score: float, sentiment_confidence: float):
        """Save news article with sentiment to BigQuery"""
        if not self.client:
            return
            
        try:
            table_id = f"{self.project_id}.{self.dataset_id}.news_articles"
            
            row = {
                "id": f"{symbol}_{int(datetime.now().timestamp())}_{hash(url) % 10000}",
                "symbol": symbol,
                "title": title,
                "content": content,
                "url": url,
                "source": source,
                "published_date": published_date.isoformat(),
                "sentiment_score": float(sentiment_score),
                "sentiment_confidence": float(sentiment_confidence),
                "timestamp": datetime.now().isoformat()
            }
            
            errors = self.client.insert_rows_json(table_id, [row])
            if errors:
                st.warning(f"BigQuery news insert errors: {errors}")
                
        except Exception as e:
            st.warning(f"Error saving news article to BigQuery: {str(e)}")
    
    def get_recent_stock_data(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get recent stock data for a symbol from BigQuery"""
        if not self.client:
            return []
            
        try:
            query = f"""
                SELECT * FROM `{self.project_id}.{self.dataset_id}.stock_data`
                WHERE symbol = @symbol 
                AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @hours HOUR)
                ORDER BY timestamp DESC
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                    bigquery.ScalarQueryParameter("hours", "INT64", hours),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            st.warning(f"Error fetching stock data from BigQuery: {str(e)}")
            return []
    
    def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get recent news articles for a symbol from BigQuery"""
        if not self.client:
            return []
            
        try:
            query = f"""
                SELECT * FROM `{self.project_id}.{self.dataset_id}.news_articles`
                WHERE symbol = @symbol 
                ORDER BY published_date DESC 
                LIMIT @limit
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            st.warning(f"Error fetching news from BigQuery: {str(e)}")
            return []
    
    def get_sentiment_summary(self, symbol: str) -> Optional[Dict]:
        """Get sentiment summary for a symbol from BigQuery"""
        if not self.client:
            return None
            
        try:
            query = f"""
                SELECT * FROM `{self.project_id}.{self.dataset_id}.stock_sentiment`
                WHERE symbol = @symbol 
                AND calculated_date = CURRENT_DATE()
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                return dict(row)
            return None
            
        except Exception as e:
            st.warning(f"Error fetching sentiment summary from BigQuery: {str(e)}")
            return None
    
    def update_sentiment_summary(self, symbol: str):
        """Calculate and update sentiment summary for a symbol in BigQuery"""
        if not self.client:
            return
            
        try:
            # First, calculate sentiment metrics from recent articles
            query = f"""
                SELECT 
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as total_articles,
                    COUNTIF(sentiment_score > 3.5) as positive_articles,
                    COUNTIF(sentiment_score < 2.5) as negative_articles,
                    COUNTIF(sentiment_score BETWEEN 2.5 AND 3.5) as neutral_articles
                FROM `{self.project_id}.{self.dataset_id}.news_articles`
                WHERE symbol = @symbol 
                AND published_date > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("symbol", "STRING", symbol),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            for row in results:
                if row.avg_sentiment is not None:
                    # Insert or update sentiment summary
                    sentiment_row = {
                        "id": f"{symbol}_{datetime.now().strftime('%Y%m%d')}",
                        "symbol": symbol,
                        "avg_sentiment": float(row.avg_sentiment),
                        "total_articles": int(row.total_articles),
                        "positive_articles": int(row.positive_articles),
                        "negative_articles": int(row.negative_articles),
                        "neutral_articles": int(row.neutral_articles),
                        "calculated_date": datetime.now().date().isoformat(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    table_id = f"{self.project_id}.{self.dataset_id}.stock_sentiment"
                    errors = self.client.insert_rows_json(table_id, [sentiment_row])
                    if errors:
                        st.warning(f"BigQuery sentiment update errors: {errors}")
                        
        except Exception as e:
            st.warning(f"Error updating sentiment summary in BigQuery: {str(e)}")
    
    def get_all_symbols_with_data(self) -> List[str]:
        """Get all symbols that have data in BigQuery"""
        if not self.client:
            return []
            
        try:
            query = f"""
                SELECT DISTINCT symbol FROM `{self.project_id}.{self.dataset_id}.stock_data`
                WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
                ORDER BY symbol
            """
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            return [row.symbol for row in results]
            
        except Exception as e:
            st.warning(f"Error fetching symbols from BigQuery: {str(e)}")
            return []