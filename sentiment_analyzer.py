import os
import json
from typing import Dict, List, Any
import streamlit as st

class SentimentAnalyzer:
    """Simple sentiment analysis without external APIs"""
    
    def __init__(self):
        # Simple keyword-based sentiment analysis
        self.positive_words = {
            'growth', 'profit', 'increase', 'gain', 'bull', 'bullish', 'rise', 'up', 
            'higher', 'strong', 'beat', 'exceed', 'outperform', 'success', 'positive',
            'upgrade', 'buy', 'recommend', 'optimistic', 'rally', 'surge', 'boost',
            'excellent', 'good', 'great', 'improve', 'expansion', 'revenue'
        }
        
        self.negative_words = {
            'loss', 'decline', 'bear', 'bearish', 'fall', 'drop', 'down', 'lower',
            'weak', 'miss', 'underperform', 'fail', 'negative', 'downgrade', 'sell',
            'pessimistic', 'crash', 'plunge', 'worry', 'concern', 'risk', 'poor',
            'bad', 'terrible', 'cut', 'reduce', 'layoff', 'bankruptcy'
        }
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text using keyword matching
        Returns sentiment score (1-5) and confidence (0-1)
        """
        if not text:
            return {'rating': 3.0, 'confidence': 0.0}
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if any(pos in word for pos in self.positive_words))
        negative_count = sum(1 for word in words if any(neg in word for neg in self.negative_words))
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return {'rating': 3.0, 'confidence': 0.1}  # Neutral with low confidence
        
        # Calculate sentiment score (1-5 scale)
        if positive_count > negative_count:
            intensity = min(positive_count - negative_count, 5)
            rating = 3.0 + (intensity * 0.4)  # 3.0 to 5.0
        elif negative_count > positive_count:
            intensity = min(negative_count - positive_count, 5)
            rating = 3.0 - (intensity * 0.4)  # 3.0 to 1.0
        else:
            rating = 3.0  # Neutral
        
        # Calculate confidence based on number of sentiment words found
        confidence = min(total_sentiment_words / 10.0, 1.0)
        
        return {
            'rating': max(1.0, min(5.0, rating)),
            'confidence': max(0.1, confidence)
        }
    
    def get_sentiment_label(self, rating: float) -> str:
        """Convert numeric rating to label"""
        if rating >= 4.0:
            return "Very Positive"
        elif rating >= 3.5:
            return "Positive"
        elif rating > 2.5:
            return "Neutral"
        elif rating >= 2.0:
            return "Negative"
        else:
            return "Very Negative"
    
    def get_sentiment_color(self, rating: float) -> str:
        """Get color for sentiment display"""
        if rating >= 3.5:
            return "green"
        elif rating >= 2.5:
            return "gray"
        else:
            return "red"
    
    def analyze_multiple_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment for multiple articles and return summary"""
        if not articles:
            return {
                'average_sentiment': 3.0,
                'total_articles': 0,
                'positive_articles': 0,
                'negative_articles': 0,
                'neutral_articles': 0,
                'confidence': 0.0
            }
        
        sentiments = []
        confidences = []
        
        for article in articles:
            # Combine title and content for analysis
            text = f"{article.get('title', '')} {article.get('content', '')}"
            result = self.analyze_text_sentiment(text)
            sentiments.append(result['rating'])
            confidences.append(result['confidence'])
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        avg_confidence = sum(confidences) / len(confidences)
        
        positive_count = len([s for s in sentiments if s >= 3.5])
        negative_count = len([s for s in sentiments if s < 2.5])
        neutral_count = len(sentiments) - positive_count - negative_count
        
        return {
            'average_sentiment': avg_sentiment,
            'total_articles': len(articles),
            'positive_articles': positive_count,
            'negative_articles': negative_count,
            'neutral_articles': neutral_count,
            'confidence': avg_confidence
        }

# Create a fallback OpenAI-like interface for when API key is available
class OpenAISentimentAnalyzer:
    """OpenAI-powered sentiment analysis (requires API key)"""
    
    def __init__(self):
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.has_openai = bool(self.openai_api_key)
        
        if self.has_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_api_key)
            except ImportError:
                self.has_openai = False
                st.warning("OpenAI library not installed. Using basic sentiment analysis.")
            except Exception:
                self.has_openai = False
                st.warning("OpenAI API key invalid. Using basic sentiment analysis.")
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using OpenAI or fallback to simple analysis"""
        if not self.has_openai:
            # Fallback to simple analysis
            analyzer = SentimentAnalyzer()
            return analyzer.analyze_text_sentiment(text)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": "You are a sentiment analysis expert. "
                        + "Analyze the sentiment of the text and provide a rating "
                        + "from 1 to 5 stars and a confidence score between 0 and 1. "
                        + "Respond with JSON in this format: "
                        + "{'rating': number, 'confidence': number}",
                    },
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "rating": max(1, min(5, round(result["rating"]))),
                "confidence": max(0, min(1, result["confidence"])),
            }
        except Exception as e:
            # Fallback to simple analysis on error
            analyzer = SentimentAnalyzer()
            return analyzer.analyze_text_sentiment(text)