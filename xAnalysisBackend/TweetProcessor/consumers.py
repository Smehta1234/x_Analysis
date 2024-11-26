from datetime import datetime, timedelta
import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import os
from TweetProcessingFiles.Scraper import scrape_twitter
from TweetProcessingFiles.FinalAnalysisSummary import generate_summary
from TweetProcessingFiles.FinalAnalysisSentiments import generate_graph_statistics


class KeywordConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the keyword from the URL route
        self.keyword = self.scope['url_route']['kwargs']['keyword']
        self.room_group_name = f"keyword_{self.keyword}"
        self.api_key = os.getenv('GROQ_API_KEY')  # Load API key from environment

        print(f"Starting scraper for keyword: {self.keyword}")

        # Accept the WebSocket connection
        await self.accept()

        # Define the date range for scraping
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d")

        # Start the scraper as a background task
        asyncio.create_task(self.run_scraper(self.keyword))

        # Start concurrent tasks for summary and graph generation
        asyncio.create_task(self.run_summary_loop())
        asyncio.create_task(self.run_graph_statistics_loop())

    async def run_scraper(self, keyword):
        """Runs the scraper in a background thread."""
        await asyncio.to_thread(scrape_twitter, keyword)

    async def run_summary_loop(self):
        """Continuously generates summaries and sends to frontend."""
        while True:
            try:
                # Run the generate_summary function
                summary = await asyncio.to_thread(generate_summary, self.keyword, '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', top_k=10)

                # Handle empty summary
                if not summary:
                    summary = "No summary available for the current keyword."

                # Send the summary to the frontend
                await self.send(text_data=json.dumps({
                    'type': 'summary',
                    'data': summary
                }))
            except Exception as e:
                print(f"Error in run_summary_loop: {e}")

            # Wait some time before generating the next summary
            await asyncio.sleep(20)  # Adjust the interval as needed

    async def run_graph_statistics_loop(self):
        """Continuously generates graph statistics and sends to frontend."""
        while True:
            try:
                # Run the generate_graph_statistics function
                graph_data = await asyncio.to_thread(generate_graph_statistics)

                # Handle empty graph data
                if not graph_data:
                    graph_data = {
                        "engagement": {},
                        "overall_sentiment_score": 0,
                        "category_sentiments": {}
                    }

                # Send the graph data to the frontend
                await self.send(text_data=json.dumps({

                    'type': 'graph_statistics',
                    'data': graph_data
                }))
            except Exception as e:
                print(f"Error in run_graph_statistics_loop: {e}")

            # Wait some time before generating the next graph statistics
            await asyncio.sleep(2)  # Adjust the interval as needed

    async def disconnect(self, close_code):
        # Remove this connection from the keyword-specific group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Process received message
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        print(message)
        # Broadcast the message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        message = event['message']
        await self.send(text_data=json.dumps({
            'messages': message
        }))
