# xAnalysis 🚀

## Overview
**xAnalysis** is a powerful tool designed to scrape data from **X (formerly Twitter)**, perform **sentiment analysis**, and provide **insights** on trending discussions. 

With this project, businesses like **Zomato** can monitor social media sentiment and get **real-time insights** into customer feedback, brand perception, and trending topics.

## Features 🛠️
- **Scrape Tweets** from X based on keywords, hashtags, or user accounts.
- **Sentiment Analysis** to classify tweets as **positive, negative, or neutral**.
- **Score Tweets** on a scale from **-1 to 1** for deeper analysis.
- **Summarize Discussions** by extracting key takeaways.
- **Provide Insights** for brands to understand customer sentiments and trends.

## Use Case 📊
Companies like **Zomato** can leverage xAnalysis to:
- Track customer opinions about their brand.
- Identify emerging trends in the food industry.
- Respond to customer concerns proactively.
- Monitor competitors’ brand perception.

## Installation & Setup ⚙️
### Prerequisites
- Python 3.x
- Tweepy / snscrape (for X scraping)
- NLP libraries (e.g., NLTK, TextBlob, VADER, Hugging Face models)

### Installation Steps
```bash
# Clone the repository
git clone https://github.com/Utkarsh09102004/xAnalysis.git
cd xAnalysis

# Install dependencies
pip install -r requirements.txt
```

## Usage 🚀
```python
from x_analysis import Scraper, SentimentAnalyzer

# Scrape tweets
scraper = Scraper(keyword='Zomato', count=100)
tweets = scraper.get_tweets()

# Analyze sentiment
analyzer = SentimentAnalyzer()
results = analyzer.get_sentiment_scores(tweets)

# Print results
print(results)
```

## Output Example 📊
| Tweet | Sentiment | Score (-1 to 1) |
|--------|------------|------------|
| "Zomato delivery is super fast! 🍕" | Positive | 0.8 |
| "Bad experience with Zomato today." | Negative | -0.6 |
| "Zomato's new feature is interesting." | Neutral | 0.1 |

## Contributors ✨
- **Utkarsh09102004** - [GitHub](https://github.com/Utkarsh09102004)
- **[Smehta1234]** - [GitHub](https://github.com/Smehta1234)

## License 📜
This project is **open-source** under the [MIT License](LICENSE).

 
 
