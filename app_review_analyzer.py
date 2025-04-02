import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google_play_scraper import reviews, app, Sort
from typing import List, Dict, Tuple
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PlayStoreReviewAnalyzer:
    def __init__(self, app_id: str, lang: str = 'en', country: str = 'us'):
        """
        Initialize the analyzer with app details.
        
        Args:
            app_id (str): The Google Play Store app ID
            lang (str): Language code for reviews (default: 'en')
            country (str): Country code for reviews (default: 'us')
        """
        self.app_id = app_id
        self.lang = lang
        self.country = country
        self.reviews = []  # Initialize reviews list
        self.app_info = None
        
        # Initialize Claude client
        self.claude = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def fetch_app_info(self) -> Dict:
        """Fetch basic app information from Play Store."""
        try:
            self.app_info = app(self.app_id, lang=self.lang, country=self.country)
            return self.app_info
        except Exception as e:
            raise Exception(f"Error fetching app info: {str(e)}")
    
    def fetch_reviews(self, count: int = 100) -> List:
        """
        Fetch reviews from Play Store.
        
        Args:
            count (int): Number of reviews to fetch (default: 100)
            
        Returns:
            List: List of reviews
        """
        try:
            # Fetch reviews using google-play-scraper
            reviews_result, _ = reviews(
                self.app_id,
                lang=self.lang,
                country=self.country,
                count=count,
                sort=Sort.NEWEST  # Use the Sort enum from the library
            )
            self.reviews = reviews_result  # Store reviews in the instance variable
            return reviews_result
        except Exception as e:
            raise Exception(f"Error fetching reviews: {str(e)}")
    
    def analyze_sentiment(self, review_text: str) -> Dict:
        """
        Analyze sentiment and topics of a review using Claude API.
        
        Args:
            review_text (str): The review text to analyze
            
        Returns:
            Dict: Dictionary containing sentiment and topics
        """
        prompt = f"""Analyze this app review and provide a JSON response with the following structure:
{{
    "sentiment": "positive/negative/neutral",
    "topics": ["topic1", "topic2", ...],
    "issues": ["issue1", "issue2", ...],
    "praises": ["praise1", "praise2", ...]
}}

Review text: {review_text}

Respond ONLY with the JSON object, no other text."""

        try:
            response = self.claude.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=1000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Get the response text and clean it
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")
                
            json_str = response_text[start_idx:end_idx]
            
            # Parse the JSON
            analysis = json.loads(json_str)
            
            # Validate the response structure
            required_keys = ["sentiment", "topics", "issues", "praises"]
            if not all(key in analysis for key in required_keys):
                raise ValueError("Response missing required keys")
                
            # Validate sentiment value
            if analysis["sentiment"] not in ["positive", "negative", "neutral", "mixed"]:
                raise ValueError(f"Invalid sentiment value: {analysis['sentiment']}")
            
            # Convert mixed sentiment to neutral
            if analysis["sentiment"] == "mixed":
                analysis["sentiment"] = "neutral"
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
            return {
                "sentiment": "neutral",
                "topics": ["error"],
                "issues": [],
                "praises": []
            }
    
    def analyze_reviews(self) -> Dict:
        """
        Analyze all reviews and generate insights.
        
        Returns:
            Dict: Dictionary containing analysis results
        """
        if not self.reviews:
            raise ValueError("Please fetch reviews first using fetch_reviews()")
            
        # Convert reviews to DataFrame for easier analysis
        reviews_df = pd.DataFrame(self.reviews)
            
        # Basic statistics
        stats = {
            "total_reviews": len(reviews_df),
            "average_rating": reviews_df['score'].mean(),
            "rating_distribution": reviews_df['score'].value_counts().to_dict(),
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "common_topics": {},
            "common_issues": {},
            "common_praises": {}
        }
        
        # Analyze each review
        for _, review in reviews_df.iterrows():
            analysis = self.analyze_sentiment(review['content'])
            stats["sentiment_distribution"][analysis["sentiment"]] += 1
            
            # Count topics
            for topic in analysis["topics"]:
                stats["common_topics"][topic] = stats["common_topics"].get(topic, 0) + 1
                
            # Count issues
            for issue in analysis["issues"]:
                stats["common_issues"][issue] = stats["common_issues"].get(issue, 0) + 1
                
            # Count praises
            for praise in analysis["praises"]:
                stats["common_praises"][praise] = stats["common_praises"].get(praise, 0) + 1
        
        # Sort dictionaries by frequency
        stats["common_topics"] = dict(sorted(stats["common_topics"].items(), key=lambda x: x[1], reverse=True))
        stats["common_issues"] = dict(sorted(stats["common_issues"].items(), key=lambda x: x[1], reverse=True))
        stats["common_praises"] = dict(sorted(stats["common_praises"].items(), key=lambda x: x[1], reverse=True))
        
        return stats
    
    def visualize_sentiment(self, save_path: str = None):
        """
        Create visualization of sentiment distribution.
        
        Args:
            save_path (str, optional): Path to save the plot
        """
        if not self.reviews:
            raise ValueError("Please fetch reviews first using fetch_reviews()")
            
        # Convert reviews to DataFrame for visualization
        reviews_df = pd.DataFrame(self.reviews)
            
        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Rating Distribution
        sns.countplot(data=reviews_df, y='score', ax=ax1)
        ax1.set_title(f"Rating Distribution for {self.app_info['title']}")
        ax1.set_xlabel("Count")
        ax1.set_ylabel("Rating")
        
        # Plot 2: Sentiment Distribution
        sentiment_data = pd.DataFrame({
            'Sentiment': list(self.analyze_reviews()['sentiment_distribution'].keys()),
            'Count': list(self.analyze_reviews()['sentiment_distribution'].values())
        })
        sns.barplot(data=sentiment_data, x='Count', y='Sentiment', ax=ax2)
        ax2.set_title("Sentiment Distribution")
        ax2.set_xlabel("Count")
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
        plt.show()
    
    def generate_report(self, output_dir: str = "reports"):
        """
        Generate a comprehensive report of the analysis.
        
        Args:
            output_dir (str): Directory to save the report
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Fetch data if not already done
        if self.app_info is None:
            self.fetch_app_info()
        if not self.reviews:
            self.fetch_reviews()
            
        # Generate analysis
        analysis = self.analyze_reviews()
        
        # Create report with only essential information
        report = {
            "app_info": {
                "title": self.app_info.get('title'),
                "developer": self.app_info.get('developer'),
                "score": self.app_info.get('score'),
                "reviews": self.app_info.get('reviews'),
                "installs": self.app_info.get('installs'),
                "price": self.app_info.get('price'),
                "size": self.app_info.get('size'),
                "updated": self.app_info.get('updated'),
                "content_rating": self.app_info.get('contentRating')
            },
            "analysis": {
                "total_reviews": analysis['total_reviews'],
                "average_rating": analysis['average_rating'],
                "rating_distribution": analysis['rating_distribution'],
                "sentiment_distribution": analysis['sentiment_distribution'],
                "common_topics": analysis['common_topics'],
                "common_issues": analysis['common_issues'],
                "common_praises": analysis['common_praises']
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # Save report
        report_path = os.path.join(output_dir, f"{self.app_id}_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate visualization
        self.visualize_sentiment(os.path.join(output_dir, f"{self.app_id}_sentiment.png"))
        
        return report_path

def main():
    # Example usage
    app_id = "com.nianticlabs.pokemongo"  # Example: Pokémon GO
    analyzer = PlayStoreReviewAnalyzer(app_id)
    
    # Fetch data
    analyzer.fetch_app_info()
    analyzer.fetch_reviews(count=100)
    
    # Generate report
    report_path = analyzer.generate_report()
    print(f"Report generated at: {report_path}")

if __name__ == "__main__":
    main() 