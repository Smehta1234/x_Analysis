import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xAnalysisBackend.settings")
django.setup()

from TweetProcessor.models import Tweet  # Import your models after Django setup


def remove_first_n_tweets(n=20):
    """
    Deletes the first n rows from the Tweet table.

    Args:
        n (int): The number of rows to delete.
    """
    try:
        # Fetch the first n tweets
        tweets_to_delete = list(Tweet.objects.all()[:n])  # Convert to a list to avoid using slicing with delete()

        # Delete the fetched tweets one by one or as a batch
        for tweet in tweets_to_delete:
            tweet.delete()

        print(f"The first {n} rows from the Tweet table have been deleted.")
    except Exception as e:
        print(f"An error occurred while deleting rows from the Tweet table: {e}")


# Run the function
if __name__ == "__main__":
    remove_first_n_tweets(20)  # Delete the first 20 rows
