import pandas as pd
import re
from django.db.models import Sum, Count, Avg
from TweetProcessor.models import Tweet

def generate_graph_statistics():
    """
    Analyze tweets stored in the database and return summary statistics in the desired format.

    Returns:
        dict: A dictionary containing:
            - total number of tweets processed
            - overall sentiment score (rounded to 2 decimal places)
            - category sentiments as a list of dictionaries
            - engagement summarized by sentiment type in the desired format
    """
    # Fetch tweets from the database
    tweets = Tweet.objects.all().values(
        "text", "likes", "comments", "bookmarks", "reposts", "views", "sentiment_score"
    )
    df = pd.DataFrame(tweets)  # Convert queryset to pandas DataFrame

    if df.empty:
        return {
            "type": "graph_statistics",
            "data": {
                "total_tweets": 0,
                "overall_sentiment_score": 0,
                "category_sentiments": [],
                "engagement": [
                    {"name": "Positive", "value": 0},
                    {"name": "Neutral", "value": 0},
                    {"name": "Negative", "value": 0},
                ],
            },
        }

    # Total number of tweets processed
    total_tweets = len(df)

    # Step 1: Data Cleaning - Remove URLs, mentions, hashtags, and newline characters
    def clean_text(text):
        text = re.sub(r"http\S+", "", text)  # Remove URLs
        text = re.sub(r"@\w+", "", text)  # Remove mentions
        text = re.sub(r"#\w+", "", text)  # Remove hashtags
        text = re.sub(r"\n", " ", text)  # Remove newline characters
        return text.strip()

    df["cleaned_text"] = df["text"].apply(clean_text)

    # Step 2: Sentiment Classification - Positive, Negative, or Neutral
    def classify_sentiment(score):
        if score > 0:
            return "Positive"
        elif score < 0:
            return "Negative"
        else:
            return "Neutral"

    df["sentiment"] = df["sentiment_score"].apply(classify_sentiment)

    # Step 3: Categorize tweets based on keywords
    categories = {
        "Delivery Issue": ["delivery", "delay", "time", "issue", "problem"],
        "Customer Service": ["support", "help", "service", "agent", "contact"],
        "Food Quality": ["food", "quality", "taste", "fresh", "stale"],
        "Pricing": ["price", "cost", "expensive", "cheap", "worth"],
        "App Functionality": ["app", "application", "interface", "crash", "bug"],
        "Order Experience": ["order", "experience", "smooth", "cancel", "failed"],
        "Refund/Payment": ["refund", "payment", "money", "transaction", "credit"],
    }

    def categorize_tweet(text):
        for category, keywords in categories.items():
            if any(keyword in text.lower() for keyword in keywords):
                return category
        return "Other"

    df["category"] = df["cleaned_text"].apply(categorize_tweet)

    # Step 4: Sentiment breakdown by category
    category_sentiments_raw = df.groupby(["category", "sentiment"]).size().unstack(fill_value=0)

    # Convert category sentiments into a list of dictionaries
    category_sentiments = []
    for category, row in category_sentiments_raw.iterrows():
        if category == "Other":
            continue
        category_sentiments.append({
            "name": category,
            "positive": int(row.get("Positive", 0)),  # Ensure Python int
            "negative": int(row.get("Negative", 0)),  # Ensure Python int
            "neutral": int(row.get("Neutral", 0)),    # Ensure Python int
        })

    # Step 5: Engagement over positive/negative/neutral tweets (excluding "views")
    engagement_raw = df.groupby("sentiment")[["likes", "comments", "bookmarks", "reposts"]].sum()
    engagement = [
        {"name": "Positive", "value": int(engagement_raw.loc["Positive"].sum())} if "Positive" in engagement_raw.index else {"name": "Positive", "value": 0},
        {"name": "Neutral", "value": int(engagement_raw.loc["Neutral"].sum())} if "Neutral" in engagement_raw.index else {"name": "Neutral", "value": 0},
        {"name": "Negative", "value": int(engagement_raw.loc["Negative"].sum())} if "Negative" in engagement_raw.index else {"name": "Negative", "value": 0},
    ]

    # Step 6: Overall Sentiment Score
    overall_sentiment_score = round(float(df["sentiment_score"].mean()), 2)  # Rounded to 2 decimal places

    # Return results as a dictionary in the desired structure
    return {
        "type": "graph_statistics",
        "data": {
            "total_tweets": total_tweets,
            "overall_sentiment_score": overall_sentiment_score,
            "category_sentiments": category_sentiments,
            "engagement": engagement,
        },
    }
