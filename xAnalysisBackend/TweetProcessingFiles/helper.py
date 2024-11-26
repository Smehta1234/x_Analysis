from sqlalchemy import create_engine, Column, String, Integer, Float, Text, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from textblob import TextBlob
from sentence_transformers import SentenceTransformer
import spacy
import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


# Database connection setup
DATABASE_URL = "postgresql://postgres:Utkarsh123#@database-1.c9gqocyo2sie.ap-south-1.rds.amazonaws.com:5432/postgres"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Load models globally
nlp = spacy.load("en_core_web_sm")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


# Define database models
class Tweet(Base):
    __tablename__ = 'tweets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    bookmarks = Column(Integer, default=0)
    reposts = Column(Integer, default=0)
    views = Column(Integer, default=0)
    sentiment = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    embeddings = Column(Text, nullable=True)
    unique_identifier = Column(String, unique=True, nullable=False)

    keywords = relationship("Keyword", secondary="tweet_keywords", back_populates="tweets")


class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String, unique=True, nullable=False)

    tweets = relationship("Tweet", secondary="tweet_keywords", back_populates="keywords")


# Association table for many-to-many relationship
tweet_keywords = Table(
    'tweet_keywords',
    Base.metadata,
    Column('tweet_id', Integer, ForeignKey('tweets.id'), primary_key=True),
    Column('keyword_id', Integer, ForeignKey('keywords.id'), primary_key=True)
)

# Create tables in the database
Base.metadata.create_all(engine)


# Helper functions
def get_single_tweet_sentiment(tweet_text):
    analysis = TextBlob(tweet_text)
    polarity = analysis.sentiment.polarity

    if polarity > 0:
        sentiment = 'Positive'
    elif polarity < 0:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    return {'sentiment': sentiment, 'sentiment_score': polarity}


def generate_embeddings(text):
    embeddings = embedding_model.encode(text)
    return embeddings.tolist()


def extract_keywords(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN") and not token.is_stop]
    return keywords


# Process a single tweet and store in the database
def process_tweet(tweet_data):
    text = tweet_data.get('text', '')
    date = tweet_data.get('date', '')
    time = tweet_data.get('time', '')
    likes = int(tweet_data.get('likes', 0))
    replies = int(tweet_data.get('replies', 0))
    reposts = int(tweet_data.get('reposts', 0))
    bookmarks = int(tweet_data.get('bookmarks', 0))
    views = int(tweet_data.get('views', 0))

    sentiment_analysis = get_single_tweet_sentiment(text)
    sentiment = sentiment_analysis['sentiment']
    sentiment_score = sentiment_analysis['sentiment_score']
    embeddings = generate_embeddings(text)

    # Generate unique identifier (e.g., hash of text + date + time)
    unique_id = f"{text}-{date}-{time}"

    # Check if tweet already exists
    if session.query(Tweet).filter_by(unique_identifier=unique_id).first():
        print("Tweet already exists in the database.")
        return

    # Create a new Tweet object
    tweet = Tweet(
        text=text,
        date=date,
        time=time,
        likes=likes,
        comments=replies,
        bookmarks=bookmarks,
        reposts=reposts,
        views=views,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        embeddings=str(embeddings),  # Store embeddings as a string
        unique_identifier=unique_id
    )

    # Add tweet to the session
    session.add(tweet)

    # Extract keywords and associate them with the tweet
    keywords = extract_keywords(text)
    for keyword_text in keywords:
        keyword = session.query(Keyword).filter_by(word=keyword_text).first()
        if not keyword:
            keyword = Keyword(word=keyword_text)
            session.add(keyword)
        tweet.keywords.append(keyword)

    # Commit the transaction
    session.commit()
    print(f"Tweet added to database: {tweet.text[:50]}")


# Selenium logic
def initialize_browser():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    browser = webdriver.Chrome(options=options)
    actions = ActionChains(browser)
    return browser, actions


def login_to_twitter(browser, wait, username, password, verification=None):
    try:
        browser.get("https://x.com/i/flow/login")
        username_input = wait.until(EC.presence_of_element_located((By.NAME, 'text')))
        username_input.send_keys(username)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()

        if verification:
            verification_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-text-id='ocfEnterTextTextInput']"))
            )
            verification_input.send_keys(verification)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))).click()

        password_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
        password_input.send_keys(password)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))).click()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False


def search_twitter(browser, wait, search_term, start_date, end_date):
    try:
        search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        search_query = f"{search_term} since:{start_date} until:{end_date}"
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
    except Exception as e:
        print(f"Search failed: {e}")


def collect_tweets_and_process(browser, wait):
    try:
        match = False
        while not match:
            tweet_elements = browser.find_elements(By.CSS_SELECTOR, 'div[data-testid="cellInnerDiv"]')
            for tweet_element in tweet_elements:
                try:
                    tweet_text = " ".join([span.text for span in tweet_element.find_elements(By.XPATH, ".//div[@data-testid='tweetText']//span")])
                    tweet_datetime = tweet_element.find_element(By.XPATH, ".//time").get_attribute("datetime")
                    tweet_date, tweet_time = tweet_datetime.split("T")
                    tweet_time = tweet_time.split(".")[0]

                    engagement_text = tweet_element.find_element(By.XPATH, ".//div[@role='group']").get_attribute("aria-label")
                    replies = reposts = likes = bookmarks = views = 0
                    if engagement_text:
                        for part in engagement_text.split(", "):
                            if "replies" in part:
                                replies = int(part.split()[0].replace(",", ""))
                            elif "reposts" in part:
                                reposts = int(part.split()[0].replace(",", ""))
                            elif "likes" in part:
                                likes = int(part.split()[0].replace(",", ""))
                            elif "views" in part:
                                views = int(part.split()[0].replace(",", ""))

                    tweet_data = {
                        "text": tweet_text,
                        "date": tweet_date,
                        "time": tweet_time,
                        "likes": likes,
                        "replies": replies,
                        "reposts": reposts,
                        "views": views
                    }
                    process_tweet(tweet_data)

                except Exception as e:
                    print(f"Error processing tweet: {e}")

            last_count = browser.execute_script("return document.body.scrollHeight")
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_count = browser.execute_script("return document.body.scrollHeight")
            if last_count == new_count:
                match = True
        print("Tweet collection complete.")
    except Exception as e:
        print(f"Error collecting tweets: {e}")


def main():
    username = "_UtkarshAg"  # Replace with your Twitter username
    password = "Utkarsh123#"  # Replace with your Twitter password
    verification = None  # Add verification code if required

    search_term = "zomato"
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    browser, actions = initialize_browser()
    wait = WebDriverWait(browser, 15)

    try:
        if login_to_twitter(browser, wait, username, password, verification):
            search_twitter(browser, wait, search_term, start_date, end_date)
            collect_tweets_and_process(browser, wait)
    finally:
        browser.quit()


if __name__ == "__main__":
    main()
