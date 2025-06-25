import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

class NewsSimulator:
    """Generate realistic news articles and sentiment for stock dashboard"""
    
    def __init__(self):
        self.company_data = {
            'AAPL': 'Apple Inc.',
            'GOOGL': 'Alphabet Inc.',
            'MSFT': 'Microsoft Corporation',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'NFLX': 'Netflix Inc.',
            'AMD': 'Advanced Micro Devices',
            'INTC': 'Intel Corporation',
            'CRM': 'Salesforce Inc.',
            'UBER': 'Uber Technologies',
            'SPOT': 'Spotify Technology',
            'JPM': 'JPMorgan Chase',
            'V': 'Visa Inc.',
            'JNJ': 'Johnson & Johnson',
            'WMT': 'Walmart Inc.',
            'PG': 'Procter & Gamble',
            'HD': 'Home Depot',
            'BAC': 'Bank of America',
            'DIS': 'Walt Disney Company',
            'ADBE': 'Adobe Inc.',
            'PYPL': 'PayPal Holdings',
            'CMCSA': 'Comcast Corporation',
            'PFE': 'Pfizer Inc.',
            'VZ': 'Verizon Communications',
            'T': 'AT&T Inc.',
            'KO': 'Coca-Cola Company',
            'PEP': 'PepsiCo Inc.',
            'XOM': 'Exxon Mobil Corporation'
        }
        
        self.news_templates = [
            "{company} Reports {outcome} Quarterly Earnings",
            "{company} Announces New {innovation} Initiative",
            "Analysts {sentiment} on {company} Stock Performance",
            "{company} Expands Operations in {market} Market",
            "CEO Discusses {company}'s Strategic Vision",
            "{company} Stock Shows {performance} Amid Market Volatility",
            "Industry Leaders Praise {company}'s Innovation",
            "{company} Beats Market Expectations in Latest Report"
        ]
        
        self.content_templates = [
            "{company} ({symbol}) demonstrated {performance} performance this quarter with revenue {change} compared to the previous period. The company's strategic initiatives continue to drive growth across key business segments.",
            "Market analysts are {sentiment} about {company}'s future prospects following recent strategic announcements. The company's focus on innovation and market expansion appears to be yielding positive results.",
            "{company} continues to strengthen its market position through strategic investments and operational excellence. Recent financial metrics indicate sustained momentum in core business areas.",
            "Investors are closely monitoring {company} as the company navigates current market conditions. Leadership remains confident in the company's long-term strategic direction and growth potential."
        ]
    
    def generate_news_articles(self, symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Generate realistic news articles for a stock symbol"""
        company_name = self.company_data.get(symbol, f"{symbol} Corporation")
        articles = []
        
        for i in range(limit):
            # Generate varied sentiment and content
            sentiment_bias = random.choice(['positive', 'neutral', 'mixed'])
            
            # Select template and fill variables
            news_template = random.choice(self.news_templates)
            content_template = random.choice(self.content_templates)
            
            # Generate template variables based on sentiment
            if sentiment_bias == 'positive':
                outcome = random.choice(['Strong', 'Impressive', 'Record'])
                innovation = random.choice(['Technology', 'Product', 'Digital'])
                sentiment_word = random.choice(['Optimistic', 'Bullish', 'Positive'])
                performance = random.choice(['Strong', 'Resilient', 'Robust'])
                change = random.choice(['increased by 8%', 'grew significantly', 'exceeded forecasts'])
            elif sentiment_bias == 'neutral':
                outcome = random.choice(['Steady', 'Mixed', 'In-Line'])
                innovation = random.choice(['Sustainability', 'Efficiency', 'Growth'])
                sentiment_word = random.choice(['Cautious', 'Watchful', 'Neutral'])
                performance = random.choice(['steady', 'consistent', 'stable'])
                change = random.choice(['remained stable', 'met expectations', 'showed modest growth'])
            else:  # mixed
                outcome = random.choice(['Challenging', 'Mixed', 'Variable'])
                innovation = random.choice(['Restructuring', 'Optimization', 'Strategic'])
                sentiment_word = random.choice(['Mixed', 'Cautious', 'Varied'])
                performance = random.choice(['mixed', 'variable', 'evolving'])
                change = random.choice(['faced headwinds', 'showed mixed results', 'experienced volatility'])
            
            market = random.choice(['International', 'Domestic', 'Emerging', 'Digital'])
            
            title = news_template.format(
                company=company_name,
                outcome=outcome,
                innovation=innovation,
                sentiment=sentiment_word,
                market=market,
                performance=performance
            )
            
            content = content_template.format(
                company=company_name,
                symbol=symbol,
                performance=performance,
                change=change,
                sentiment=sentiment_word.lower()
            )
            
            # Generate publish time (last 24 hours)
            hours_ago = random.randint(1, 24)
            published_date = datetime.now() - timedelta(hours=hours_ago)
            
            articles.append({
                'title': title,
                'content': content,
                'url': f"https://finance.example.com/{symbol.lower()}-news-{i+1}",
                'source': random.choice(['Financial Times', 'MarketWatch', 'Reuters', 'Bloomberg']),
                'published_date': published_date,
                'symbol': symbol
            })
        
        return articles
    
    def get_sentiment_for_content(self, content: str) -> Dict[str, float]:
        """Generate realistic sentiment based on content keywords"""
        positive_words = ['strong', 'impressive', 'record', 'growth', 'exceeded', 'bullish', 'optimistic', 'positive', 'robust']
        negative_words = ['challenging', 'headwinds', 'decline', 'weak', 'concerning', 'bearish', 'negative', 'volatile']
        
        content_lower = content.lower()
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)
        
        if positive_score > negative_score:
            rating = random.uniform(3.5, 5.0)
            confidence = random.uniform(0.7, 0.9)
        elif negative_score > positive_score:
            rating = random.uniform(1.0, 2.5)
            confidence = random.uniform(0.6, 0.8)
        else:
            rating = random.uniform(2.5, 3.5)
            confidence = random.uniform(0.5, 0.7)
        
        return {
            'rating': round(rating, 1),
            'confidence': round(confidence, 2)
        }