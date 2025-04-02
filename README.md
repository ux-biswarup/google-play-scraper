# Play Store App Review Analysis Tool

This tool helps analyze Google Play Store app reviews to support better design decision-making. It combines quantitative and qualitative analysis, user research, and sentiment analysis to generate actionable insights.

## Features

- Automated review scraping from Google Play Store
- Sentiment and topic analysis of reviews
- Insight generation and visualization
- Comprehensive report generation
- Data visualization of sentiment distribution

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from app_review_analyzer import PlayStoreReviewAnalyzer

# Initialize the analyzer with an app ID
analyzer = PlayStoreReviewAnalyzer("com.example.app")

# Fetch app information
app_info = analyzer.fetch_app_info()

# Fetch reviews (default: 1000 reviews)
reviews_df = analyzer.fetch_reviews(count=100)

# Generate a comprehensive report
report_path = analyzer.generate_report()
```

### Example

```python
# Example with Pokémon GO app
analyzer = PlayStoreReviewAnalyzer("com.nianticlabs.pokemongo")
analyzer.fetch_app_info()
analyzer.fetch_reviews(count=100)
report_path = analyzer.generate_report()
print(f"Report generated at: {report_path}")
```

## Output

The tool generates:
1. A JSON report containing:
   - App information
   - Review statistics
   - Sentiment distribution
   - Common topics
2. A visualization of the rating distribution

Reports are saved in the `reports` directory by default.

## Note on Sentiment Analysis

The current implementation includes a placeholder for sentiment analysis. To use actual sentiment analysis:
1. Implement the `analyze_sentiment` method in the `PlayStoreReviewAnalyzer` class
2. Integrate with your preferred sentiment analysis API (e.g., Claude API)

## Contributing

Feel free to submit issues and enhancement requests!
