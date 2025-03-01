#🚀 xAnalysis - Social Media Sentiment & Insights

## 📌 Overview
**xAnalysis** is an advanced tool designed to **scrape data from X (formerly Twitter)**, perform **sentiment analysis**, and deliver **valuable insights** on trending discussions. 

💡 Companies like **Zomato** can leverage this tool to **monitor brand perception, track customer sentiment, and stay ahead of social media trends**.

---

## 🔥 Features
✅ **Scrape Tweets** from X using keywords, hashtags, or user handles.  
✅ **Sentiment Analysis** - Classifies tweets as **Positive, Negative, or Neutral**.  
✅ **Sentiment Scoring** - Assigns a score between **-1 (negative) to +1 (positive)**.  
✅ **Summarization** - Generates key takeaways for quick insights.  
✅ **Business Insights** - Helps brands track trends & customer feedback effectively.

---

## 🏢 Use Case - How Businesses Benefit
### For companies like **Zomato**, xAnalysis can:
🔹 **Track customer opinions** - Know what people are saying about your brand.  
🔹 **Spot trends** - Identify emerging discussions in your industry.  
🔹 **Handle feedback proactively** - Respond to customer concerns in real-time.  
🔹 **Monitor competitors** - See how your brand stacks up.

---

## ⚙️ Installation & Setup
### 📌 Prerequisites
- Python 3.x  
- Tweepy / snscrape (for scraping X)  
- NLP libraries (NLTK, TextBlob, VADER, Hugging Face models)

### 📥 Installation Steps
```bash
# Clone the repository
git clone https://github.com/Utkarsh09102004/xAnalysis.git
cd xAnalysis

# Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Usage
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

---

## 📊 Example Output
| Tweet | Sentiment | Score (-1 to 1) |
|--------|------------|------------|
| "Zomato delivery is super fast! 🍕" | Positive | 0.8 |
| "Bad experience with Zomato today." | Negative | -0.6 |
| "Zomato's new feature is interesting." | Neutral | 0.1 |

---

## 💡 Contributors
👨‍💻 **Utkarsh09102004** - [GitHub](https://github.com/Utkarsh09102004)  
👩‍💻 **[Sanchit]** - [GitHub](https://github.com/Smehta1234)  

---

## 📜 License
This project is **open-source** under the [MIT License](LICENSE).

 
 
