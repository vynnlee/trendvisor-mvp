import subprocess
import os
import uuid
from .base import BaseAgent
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_error

class CollectionAgent(BaseAgent):
    """
    This agent is responsible for collecting data.
    It listens for TASK_CREATED events and runs the data collection tool.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        # This agent only needs to listen for TASK_CREATED events.
        super().__init__("CollectionAgent", message_bus, state_store, subscribed_events=["TASK_CREATED"])

    def handle_event(self, event_type: str, payload: dict):
        """Handles a TASK_CREATED event by running the crawl_reviews tool."""
        task_id = payload.get("task_id")
        product_name = payload.get("product_name")

        if not task_id or not product_name:
            display_error(f"Invalid payload received for {event_type}: {payload}", self.agent_name)
            return

        display_event(event_type, payload, self.agent_name)
        
        try:
            display_status(f"Starting data collection for '{product_name}'.", category=self.agent_name)
            self.state_store.update_state(task_id, {"status": "COLLECTING", "collector_agent": self.agent_name})

            script_path = os.path.join(os.path.dirname(__file__), '..', 'tools', 'crawl_reviews.py')
            result = subprocess.run(
                ["python3", script_path, product_name, task_id],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            
            output_file_path = result.stdout.strip()

            display_status(f"Data collection successful. Data at: '{output_file_path}'.", category=self.agent_name)
            
            self.state_store.update_state(task_id, {"status": "COLLECTION_COMPLETE", "data_path": output_file_path})
            
            new_payload = {"task_id": task_id, "data_path": output_file_path}
            self.message_bus.publish("COLLECTION_COMPLETE", self.agent_name, new_payload)

        except subprocess.CalledProcessError as e:
            error_message = f"Data collection script failed.\nStderr: {e.stderr.strip()}"
            display_error(error_message, agent_id=self.agent_name)
            self.state_store.update_state(task_id, {"status": "COLLECTION_FAILED", "error": error_message, "failed_by": self.agent_name})
            self.message_bus.publish("TASK_FAILED", self.agent_name, {"task_id": task_id, "error": error_message})
        
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            display_error(error_message, agent_id=self.agent_name)
            self.state_store.update_state(task_id, {"status": "COLLECTION_FAILED", "error": error_message, "failed_by": self.agent_name})
            self.message_bus.publish("TASK_FAILED", self.agent_name, {"task_id": task_id, "error": error_message})

# No __main__ block needed as this is not intended to be run standalone. 