import redis
import json
import time
import threading
from typing import Callable, Dict, Any

class MessageBus:
    """A thread-safe, Redis-based message bus for inter-agent communication."""

    def __init__(self, host: str = 'localhost', port: int = 6379, channel_prefix: str = 'trendvisor:events'):
        """
        Initializes the connection pool to Redis.
        Each subscriber will get its own connection from this pool.
        """
        try:
            # Using a connection pool makes the bus thread-safe.
            self.redis_pool = redis.ConnectionPool(host=host, port=port, db=0, decode_responses=True)
            # Test the connection
            r = redis.Redis(connection_pool=self.redis_pool)
            r.ping()
            print(f"Successfully connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            raise
        
        self.channel_prefix = channel_prefix

    def publish(self, event_type: str, source_agent: str, payload: Dict[str, Any]):
        """
        Publishes an event to a channel specific to the event type.
        This allows agents to subscribe only to events they care about.
        """
        channel = f"{self.channel_prefix}:{event_type}"
        event_id = f"evt_{int(time.time() * 1000)}"
        message = {
            "event_id": event_id,
            "timestamp": time.time(),
            "event_type": event_type,
            "source_agent": source_agent,
            "payload": payload
        }
        
        try:
            r = redis.Redis(connection_pool=self.redis_pool)
            r.publish(channel, json.dumps(message))
        except redis.RedisError as e:
            print(f"Error publishing message to Redis channel '{channel}': {e}")


    def subscribe(self, callback: Callable[[str, Dict[str, Any]], None], channels: list, stop_event: threading.Event):
        """
        Subscribes to specific channels and listens for messages.
        This method is blocking and should be run in a separate thread.
        It uses a timeout to check the stop_event periodically.
        """
        try:
            r = redis.Redis(connection_pool=self.redis_pool)
            pubsub = r.pubsub(ignore_subscribe_messages=True)
            
            # Subscribe to multiple channels
            qualified_channels = [f"{self.channel_prefix}:{ch}" for ch in channels]
            if not qualified_channels:
                return 
            
            pubsub.subscribe(*qualified_channels)
            print(f"Agent subscribed to channels: {', '.join(qualified_channels)}")

            while not stop_event.is_set():
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        # The callback expects event_type and payload
                        callback(data['event_type'], data['payload'])
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Could not process message: {message.get('data')}. Error: {e}")
            
            pubsub.close()
            
        except redis.RedisError as e:
            print(f"Error in Redis subscription thread: {e}") 