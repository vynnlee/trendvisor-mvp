import redis
import json
from typing import Dict, Any, Optional

class StateStore:
    """A Redis-based state store for managing task states."""

    def __init__(self, host: str = 'localhost', port: int = 6379):
        """
        Initializes the connection to Redis.
        
        Args:
            host: Redis server host.
            port: Redis server port.
        """
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=1, decode_responses=True) # Use DB 1 to separate from pubsub
            self.redis_client.ping()
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis for StateStore: {e}")
            raise

    def _get_task_key(self, task_id: str) -> str:
        """Constructs the Redis key for a given task ID."""
        return f"task:{task_id}"

    def set_state(self, task_id: str, state_data: Dict[str, Any]):
        """
        Sets the entire state for a given task.

        Args:
            task_id: The unique identifier for the task.
            state_data: A dictionary representing the task's state.
        """
        task_key = self._get_task_key(task_id)
        # Serialize complex types like dictionaries and lists into JSON strings
        for key, value in state_data.items():
            if isinstance(value, (dict, list)):
                state_data[key] = json.dumps(value)
        self.redis_client.hset(task_key, mapping=state_data)
        print(f"State for task '{task_id}' has been set.")

    def get_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the entire state for a given task.

        Args:
            task_id: The unique identifier for the task.

        Returns:
            A dictionary representing the task's state, or None if not found.
        """
        task_key = self._get_task_key(task_id)
        state = self.redis_client.hgetall(task_key)
        if not state:
            return None
        
        # Deserialize JSON strings back into Python objects
        for key, value in state.items():
            try:
                state[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Value was not a valid JSON string, keep it as is
                pass
        return state

    def update_state(self, task_id: str, updates: Dict[str, Any]):
        """
        Updates specific fields in the state for a given task.

        Args:
            task_id: The unique identifier for the task.
            updates: A dictionary of fields to update.
        """
        task_key = self._get_task_key(task_id)
        # Serialize complex types
        for key, value in updates.items():
            if isinstance(value, (dict, list)):
                updates[key] = json.dumps(value)
        self.redis_client.hset(task_key, mapping=updates)
        print(f"State for task '{task_id}' has been updated with: {list(updates.keys())}")

    def get_field(self, task_id: str, field: str) -> Optional[Any]:
        """
        Retrieves a single field from a task's state.

        Args:
            task_id: The unique identifier for the task.
            field: The name of the field to retrieve.

        Returns:
            The value of the field, or None if not found.
        """
        task_key = self._get_task_key(task_id)
        value = self.redis_client.hget(task_key, field)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value 