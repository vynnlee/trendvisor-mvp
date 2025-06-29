import redis
import json
import time
from typing import Callable, Dict, Any

class MessageBus:
    def __init__(self, host='localhost', port=6379):
        self.redis_client = redis.Redis(host=host, port=port, db=0, decode_responses=True)
        self.pubsub = self.redis_client.pubsub(ignore_subscribe_messages=True)

    def publish(self, channel: str, message: Dict[str, Any]):
        """Publishes a message to a specific channel."""
        self.redis_client.publish(channel, json.dumps(message))

    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribes to a channel and registers a callback."""
        self.pubsub.subscribe(**{channel: callback})
        print(f"Subscribed to {channel}")

    def listen(self):
        """Starts listening for messages in a separate thread."""
        print("Listening for messages...")
        return self.pubsub.run_in_thread(sleep_time=0.1)