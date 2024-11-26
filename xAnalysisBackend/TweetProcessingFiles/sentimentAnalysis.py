import numpy as np
from textblob import TextBlob
from sentence_transformers import SentenceTransformer
import spacy


# Load models globally
nlp = spacy.load("en_core_web_sm")  # Load spaCy model once
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Load transformer model once


def get_single_tweet_sentiment(tweet_text):
    """
    Analyzes the sentiment of a given tweet using TextBlob.

    Args:
        tweet_text (str): The text of the tweet.

    Returns:
        dict: A dictionary containing the sentiment label (Positive, Negative, Neutral)
              and the sentiment score (polarity ranging from -1 to 1).
    """
    analysis = TextBlob(tweet_text)
    polarity = analysis.sentiment.polarity  # Sentiment score between -1 and 1

    # Determine the sentiment label
    if polarity > 0:
        sentiment = 'Positive'
    elif polarity < 0:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    return {
        'sentiment': sentiment,
        'sentiment_score': polarity
    }


def generate_embeddings(text):
    """
    Generates sentence embeddings for the given text using SentenceTransformer.

    Args:
        text (str): The input text.

    Returns:
        list: A list of floating-point numbers representing the embedding vector.
    """
    embeddings = embedding_model.encode(text)  # Use globally loaded model

    # Convert to a list for JSON serialization
    return embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings


def extract_keywords(text):
    """
    Extracts keywords from the given text using spaCy.

    Keywords are filtered as nouns or proper nouns that are not stop words.

    Args:
        text (str): The input text for keyword extraction.

    Returns:
        list: A list of extracted keywords.
    """
    doc = nlp(text)  # Use globally loaded spaCy model
    keywords = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN") and not token.is_stop]
    return keywords
