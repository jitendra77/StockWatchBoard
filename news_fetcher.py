import requests
import trafilatura
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any
import streamlit as st
import time

class NewsFetcher:
    """Fetch news articles related to stocks"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_yahoo_finance_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch news from Yahoo Finance for a specific stock symbol"""
        articles = []
        try:
            # Yahoo Finance news URL for specific stock
            url = f"https://finance.yahoo.com/quote/{symbol}/news"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            news_items = soup.find_all('h3', class_='Mb(5px)')[:limit]
            
            for item in news_items:
                try:
                    link_element = item.find('a')
                    if link_element:
                        title = link_element.get_text(strip=True)
                        relative_url = link_element.get('href')
                        
                        # Convert relative URL to absolute
                        if relative_url.startswith('/'):
                            article_url = f"https://finance.yahoo.com{relative_url}"
                        else:
                            article_url = relative_url
                        
                        # Fetch article content
                        content = self._extract_article_content(article_url)
                        
                        articles.append({
                            'title': title,
                            'url': article_url,
                            'content': content,
                            'source': 'Yahoo Finance',
                            'published_date': datetime.now(),  # Yahoo doesn't provide exact timestamp
                            'symbol': symbol
                        })
                        
                        # Add delay to be respectful
                        time.sleep(0.5)
                        
                except Exception as e:
                    continue  # Skip problematic articles
                    
        except Exception as e:
            st.warning(f"Error fetching Yahoo Finance news for {symbol}: {str(e)}")
        
        return articles
    
    def fetch_google_finance_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch news from Google Finance for a specific stock symbol"""
        articles = []
        try:
            # Google Finance news search
            search_query = f"{symbol} stock news"
            url = f"https://www.google.com/search?q={search_query}&tbm=nws&num={limit}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles in Google News results
            news_items = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:limit]
            
            for item in news_items:
                try:
                    title = item.get_text(strip=True)
                    
                    # Find the parent link
                    parent_link = item.find_parent('a')
                    if parent_link:
                        href = parent_link.get('href')
                        if href and '/url?q=' in href:
                            # Extract actual URL from Google redirect
                            article_url = href.split('/url?q=')[1].split('&')[0]
                            
                            # Fetch article content
                            content = self._extract_article_content(article_url)
                            
                            articles.append({
                                'title': title,
                                'url': article_url,
                                'content': content,
                                'source': 'Google News',
                                'published_date': datetime.now(),
                                'symbol': symbol
                            })
                            
                            # Add delay to be respectful
                            time.sleep(0.5)
                            
                except Exception as e:
                    continue  # Skip problematic articles
                    
        except Exception as e:
            st.warning(f"Error fetching Google News for {symbol}: {str(e)}")
        
        return articles
    
    def fetch_marketwatch_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch news from MarketWatch for a specific stock symbol"""
        articles = []
        try:
            # MarketWatch stock page
            url = f"https://www.marketwatch.com/investing/stock/{symbol.lower()}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            news_items = soup.find_all('a', class_='link')[:limit]
            
            for item in news_items:
                try:
                    title = item.get_text(strip=True)
                    relative_url = item.get('href')
                    
                    if relative_url and title:
                        # Convert relative URL to absolute
                        if relative_url.startswith('/'):
                            article_url = f"https://www.marketwatch.com{relative_url}"
                        else:
                            article_url = relative_url
                        
                        # Fetch article content
                        content = self._extract_article_content(article_url)
                        
                        articles.append({
                            'title': title,
                            'url': article_url,
                            'content': content,
                            'source': 'MarketWatch',
                            'published_date': datetime.now(),
                            'symbol': symbol
                        })
                        
                        # Add delay to be respectful
                        time.sleep(0.5)
                        
                except Exception as e:
                    continue  # Skip problematic articles
                    
        except Exception as e:
            st.warning(f"Error fetching MarketWatch news for {symbol}: {str(e)}")
        
        return articles
    
    def _extract_article_content(self, url: str) -> str:
        """Extract article content using trafilatura"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(downloaded)
                return content[:2000] if content else ""  # Limit content length
            return ""
        except Exception as e:
            return ""
    
    def fetch_all_news(self, symbol: str, limit_per_source: int = 3) -> List[Dict[str, Any]]:
        """Fetch news from multiple sources for a stock symbol"""
        all_articles = []
        
        # Fetch from different sources
        sources = [
            self.fetch_yahoo_finance_news,
            self.fetch_marketwatch_news,
            self.fetch_google_finance_news
        ]
        
        for fetch_func in sources:
            try:
                articles = fetch_func(symbol, limit_per_source)
                all_articles.extend(articles)
            except Exception as e:
                continue  # Continue with other sources if one fails
        
        # Remove duplicates based on title similarity
        unique_articles = []
        seen_titles = set()
        
        for article in all_articles:
            title_key = article['title'].lower()[:50]  # First 50 chars for similarity check
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles[:10]  # Return max 10 articles
    
    def get_company_news_keywords(self, symbol: str, company_name: str) -> List[str]:
        """Generate search keywords for a company"""
        keywords = [
            f"{symbol} stock",
            f"{symbol} earnings",
            f"{symbol} quarterly report",
            f"{company_name} news",
            f"{company_name} stock price",
            f"{symbol} financial results"
        ]
        return keywords