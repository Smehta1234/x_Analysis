from django.db import models
from datetime import datetime
import hashlib

class Keyword(models.Model):
    word = models.CharField(max_length=255, unique=True)  # Keywords must be unique

    def __str__(self):
        return self.word



class Tweet(models.Model):
    text = models.TextField()  # Tweet content
    date = models.DateField(blank=True, null=True)  # Date when the tweet was created (optional)
    time = models.TimeField(blank=True, null=True)  # Time when the tweet was created (optional)
    likes = models.IntegerField(default=0)  # Number of likes
    comments = models.IntegerField(default=0)  # Number of comments
    bookmarks = models.IntegerField(default=0)  # Number of bookmarks
    reposts = models.IntegerField(default=0)  # Number of reposts
    views = models.IntegerField(default=0)  # Number of views
    time_added = models.DateTimeField(default=datetime.now)  # Time when this tweet was added to the system
    embeddings = models.JSONField()  # Storing embeddings as JSON
    sentiment_score = models.FloatField(default=0.0)  # Sentiment score of the tweet (-1 to 1)
    unique_identifier = models.CharField(max_length=64, unique=True)  # Unique hash for the tweet

    # Many-to-many relation with Keyword
    keywords = models.ManyToManyField('Keyword', related_name="tweets")

    def __str__(self):
        return self.text[:50]  # Return the first 50 characters of the tweet

    @staticmethod
    def generate_unique_identifier(text, date, time):
        """Generate a unique hash based on the tweet text, date, and time."""

        hash_input = f"{text}-{date}-{time}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

