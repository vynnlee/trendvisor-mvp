import redis
import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

# Pydantic model for robust type validation and serialization
class TaskState(BaseModel):
    task_id: str
    status: str = "CREATED"
    goal: str
    params: Dict[str, Any] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    error_log: Optional[str] = None

class StateStore:
    """A Redis-based state store using Pydantic for data integrity."""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 1):
        """Initializes the connection to Redis."""
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
        except redis.ConnectionError as e:
            print(f"Error connecting to Redis for StateStore: {e}")
            raise

    def _get_task_key(self, task_id: str) -> str:
        """Generates the Redis key for a given task."""
        return f"task:{task_id}"

    def save_state(self, state: TaskState):
        """Saves the entire state object for a task."""
        task_key = self._get_task_key(state.task_id)
        # Pydantic's model_dump_json handles serialization
        self.redis_client.set(task_key, state.model_dump_json())

    def get_state(self, task_id: str) -> Optional[TaskState]:
        """Retrieves and validates the state for a given task."""
        task_key = self._get_task_key(task_id)
        state_json = self.redis_client.get(task_key)
        
        if not state_json:
            return None
        
        try:
            # Pydantic's model_validate_json handles deserialization and validation
            return TaskState.model_validate_json(state_json)
        except Exception as e:
            print(f"Data validation error for task {task_id}: {e}")
            return None

    def update_state(self, task_id: str, updates: Dict[str, Any]):
        """Updates specific fields in the state for a given task."""
        current_state = self.get_state(task_id)
        if current_state:
            for key, value in updates.items():
                if hasattr(current_state, key):
                    setattr(current_state, key, value)
            self.save_state(current_state)

    def log_history(self, task_id: str, event_summary: str):
        """Appends an event summary to the task's history."""
        current_state = self.get_state(task_id)
        if current_state:
            current_state.history.append(event_summary)
            self.save_state(current_state)

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

    def get_history(self, task_id: str) -> list:
        """Retrieves the full history for a task from the Redis list."""
        history_key = f"{self._get_task_key(task_id)}:history"
        return self.redis_client.lrange(history_key, 0, -1) 