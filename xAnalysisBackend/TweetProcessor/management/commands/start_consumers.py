# myapp/management/commands/start_consumers.py
from django.core.management.base import BaseCommand
from TweetProcessor.tweetConsumer import TweetConsumer
import multiprocessing, redis
from TweetProcessor.utils.redis_client import get_redis_connection

def initialize_stream_and_group():
    redis_conn = get_redis_connection()
    stream_name = "tweets_stream"
    group_name = "tweets_group"

    try:
        redis_conn.xgroup_create(stream_name, group_name, id='0', mkstream=True)
        print(f"Consumer group '{group_name}' created on stream '{stream_name}'.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" in str(e):
            print(f"Consumer group '{group_name}' already exists.")
        else:
            raise e

def start_consumer(consumer_name):
    consumer = TweetConsumer(consumer_name)
    consumer.consume_tweets()

class Command(BaseCommand):
    help = 'Starts multiple consumer processes to process Redis stream data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--num_consumers',
            type=int,
            default=3,
            help='The number of consumer processes to start'
        )

    def handle(self, *args, **options):
        num_consumers = options['num_consumers']
        processes = []

        # Initialize the stream and consumer group
        initialize_stream_and_group()

        self.stdout.write(f"Starting {num_consumers} consumer processes...")

        for i in range(num_consumers):
            consumer_name = f"consumer_{i}"
            process = multiprocessing.Process(target=start_consumer, args=(consumer_name,))
            process.start()
            processes.append(process)

        for process in processes:
            process.join()
