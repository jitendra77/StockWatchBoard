import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import streamlit as st

class DatabaseManager:
    """Database manager for stock data, news, and sentiment analysis"""
    
    def __init__(self):
        self.connection_string = os.environ.get('DATABASE_URL')
        self.init_tables()
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.connection_string)
    
    def init_tables(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Stock data table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS stock_data (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(10) NOT NULL,
                            current_price DECIMAL(10,2),
                            previous_close DECIMAL(10,2),
                            change_amount DECIMAL(10,2),
                            change_percent DECIMAL(6,3),
                            volume BIGINT,
                            market_cap BIGINT,
                            company_name VARCHAR(255),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_stock_symbol_timestamp 
                        ON stock_data (symbol, timestamp)
                    """)
                    
                    # News articles table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS news_articles (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(10) NOT NULL,
                            title TEXT NOT NULL,
                            content TEXT,
                            url VARCHAR(500) UNIQUE,
                            source VARCHAR(100),
                            published_date TIMESTAMP,
                            sentiment_score DECIMAL(3,2),
                            sentiment_confidence DECIMAL(3,2),
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for news
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_news_symbol_date 
                        ON news_articles (symbol, published_date)
                    """)
                    
                    # Stock sentiment summary table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS stock_sentiment (
                            id SERIAL PRIMARY KEY,
                            symbol VARCHAR(10) NOT NULL,
                            avg_sentiment DECIMAL(3,2),
                            total_articles INTEGER,
                            positive_articles INTEGER,
                            negative_articles INTEGER,
                            neutral_articles INTEGER,
                            calculated_date DATE,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT unique_symbol_date UNIQUE(symbol, calculated_date)
                        )
                    """)
                    
                    conn.commit()
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
    
    def save_stock_data(self, stock_data: Dict[str, Dict[str, Any]]):
        """Save stock data to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for symbol, data in stock_data.items():
                        cur.execute("""
                            INSERT INTO stock_data 
                            (symbol, current_price, previous_close, change_amount, 
                             change_percent, volume, market_cap, company_name)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            symbol,
                            data.get('current_price', 0),
                            data.get('previous_close', 0),
                            data.get('change', 0),
                            data.get('percent_change', 0),
                            data.get('volume', 0),
                            data.get('market_cap', 0),
                            data.get('company_name', symbol)
                        ))
                    conn.commit()
        except Exception as e:
            st.warning(f"Error saving stock data: {str(e)}")
    
    def save_news_article(self, symbol: str, title: str, content: str, 
                         url: str, source: str, published_date: datetime,
                         sentiment_score: float, sentiment_confidence: float):
        """Save news article with sentiment to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO news_articles 
                        (symbol, title, content, url, source, published_date, 
                         sentiment_score, sentiment_confidence)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING
                    """, (symbol, title, content, url, source, published_date,
                          sentiment_score, sentiment_confidence))
                    conn.commit()
        except Exception as e:
            st.warning(f"Error saving news article: {str(e)}")
    
    def get_recent_stock_data(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get recent stock data for a symbol"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM stock_data 
                        WHERE symbol = %s 
                        AND timestamp > NOW() - INTERVAL '%s hours'
                        ORDER BY timestamp DESC
                    """, (symbol, hours))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            st.warning(f"Error fetching stock data: {str(e)}")
            return []
    
    def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Get recent news articles for a symbol"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM news_articles 
                        WHERE symbol = %s 
                        ORDER BY published_date DESC 
                        LIMIT %s
                    """, (symbol, limit))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            st.warning(f"Error fetching news: {str(e)}")
            return []
    
    def get_sentiment_summary(self, symbol: str) -> Optional[Dict]:
        """Get sentiment summary for a symbol"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM stock_sentiment 
                        WHERE symbol = %s 
                        AND calculated_date = CURRENT_DATE
                    """, (symbol,))
                    result = cur.fetchone()
                    return dict(result) if result else None
        except Exception as e:
            st.warning(f"Error fetching sentiment summary: {str(e)}")
            return None
    
    def update_sentiment_summary(self, symbol: str):
        """Calculate and update sentiment summary for a symbol"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Calculate sentiment metrics from recent articles
                    cur.execute("""
                        SELECT 
                            AVG(sentiment_score) as avg_sentiment,
                            COUNT(*) as total_articles,
                            SUM(CASE WHEN sentiment_score > 3.5 THEN 1 ELSE 0 END) as positive_articles,
                            SUM(CASE WHEN sentiment_score < 2.5 THEN 1 ELSE 0 END) as negative_articles,
                            SUM(CASE WHEN sentiment_score BETWEEN 2.5 AND 3.5 THEN 1 ELSE 0 END) as neutral_articles
                        FROM news_articles 
                        WHERE symbol = %s 
                        AND published_date > NOW() - INTERVAL '7 days'
                    """, (symbol,))
                    
                    result = cur.fetchone()
                    
                    if result and result[0] is not None:
                        cur.execute("""
                            INSERT INTO stock_sentiment 
                            (symbol, avg_sentiment, total_articles, positive_articles, 
                             negative_articles, neutral_articles, calculated_date)
                            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE)
                            ON CONFLICT (symbol, calculated_date) 
                            DO UPDATE SET 
                                avg_sentiment = EXCLUDED.avg_sentiment,
                                total_articles = EXCLUDED.total_articles,
                                positive_articles = EXCLUDED.positive_articles,
                                negative_articles = EXCLUDED.negative_articles,
                                neutral_articles = EXCLUDED.neutral_articles,
                                timestamp = CURRENT_TIMESTAMP
                        """, (symbol, *result))
                        
                        conn.commit()
        except Exception as e:
            st.warning(f"Error updating sentiment summary: {str(e)}")
    
    def get_all_symbols_with_data(self) -> List[str]:
        """Get all symbols that have data in the database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT symbol FROM stock_data 
                        WHERE timestamp > NOW() - INTERVAL '24 hours'
                        ORDER BY symbol
                    """)
                    return [row[0] for row in cur.fetchall()]
        except Exception as e:
            st.warning(f"Error fetching symbols: {str(e)}")
            return []