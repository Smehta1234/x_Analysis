import json
import django
django.setup()  # Ensure Django is set up before using models
import datetime
from django.utils import timezone

from TweetProcessor.utils.redis_client import get_redis_connection
from TweetProcessingFiles.sentimentAnalysis import get_single_tweet_sentiment, generate_embeddings, extract_keywords
from TweetProcessor.models import Tweet, Keyword

class TweetConsumer:
    def __init__(self, consumer_name):
        # Initialize the Redis connection and stream details
        self.redis_conn = get_redis_connection()
        self.stream_name = "tweets_stream"
        self.group_name = "tweets_group"
        self.consumer_name = consumer_name

    def decode_tweet_data(self, tweet_data):
        """
        Utility function to decode both keys and values of tweet data.
        It ensures that byte-like data is decoded, and strings are kept as is.
        """
        return {
            key.decode('utf-8') if isinstance(key, bytes) else key:
            value.decode('utf-8') if isinstance(value, bytes) else value
            for key, value in tweet_data.items()
        }

    def process_tweet(self, tweet_data):
        # Decode tweet data to ensure it's in string format
        decoded_tweet_data = self.decode_tweet_data(tweet_data)

        # Extract fields from the decoded tweet data
        text = decoded_tweet_data.get('text', '')
        date = decoded_tweet_data.get('date', '')
        time = decoded_tweet_data.get('time', '')
        likes = int(decoded_tweet_data.get('likes', 0))
        replies = int(decoded_tweet_data.get('replies', 0))
        reposts = int(decoded_tweet_data.get('reposts', 0))
        bookmarks = int(decoded_tweet_data.get('bookmarks', 0))
        views = int(decoded_tweet_data.get('views', 0))

        # date = timezone.make_aware(datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"))

        # Call external functions for embeddings and sentiment analysis
        embeddings = generate_embeddings(text)
        sentiment_score = get_single_tweet_sentiment(text).get("sentiment_score", 0)

        # Generate a unique identifier for the tweet
        unique_id = Tweet.generate_unique_identifier(text, date, time)

        # Check if the tweet already exists in the database
        if Tweet.objects.filter(unique_identifier=unique_id).exists():
            print("Tweet already exists in the database.")
            return

        # Save the tweet to the database
        tweet = Tweet.objects.create(
            text=text,
            # date=date,
            # time=time,
            likes=likes,
            comments=replies,
            bookmarks=bookmarks,
            reposts=reposts,
            views=views,
            sentiment_score=sentiment_score,
            embeddings=embeddings,
            unique_identifier=unique_id
        )

        # Extract and add keywords to the tweet
        keywords = extract_keywords(text)
        for keyword_text in keywords:
            keyword, _ = Keyword.objects.get_or_create(word=keyword_text)
            tweet.keywords.add(keyword)

        tweet.save()
        print(f"Tweet added to database: {tweet.text[:50]}")

    def consume_tweets(self):
        # Continuously consume messages from the Redis stream
        while True:
            # Read new entries from the stream
            entries = self.redis_conn.xreadgroup(
                self.group_name,
                self.consumer_name,
                {self.stream_name: '>'},
                count=1,
                block=100  # Block for up to 100 ms if no new data
            )

            for stream, messages in entries:
                for message_id, tweet_data in messages:
                    try:
                        # Decode tweet data before processing
                        decoded_tweet_data = self.decode_tweet_data(tweet_data)

                        # Process the tweet with decoded data
                        self.process_tweet(decoded_tweet_data)

                        # Only acknowledge the message after successful processing
                        self.redis_conn.xack(self.stream_name, self.group_name, message_id)
                    except Exception as e:
                        # Log the error and leave the message unacknowledged for retry
                        print(f"Error processing message {message_id}: {e}")
