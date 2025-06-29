import time
import json
from .base import BaseAgent
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_error

# from airtop import Airtop, Options # This will be used later

class CollectionAgent(BaseAgent):
    """
    The CollectionAgent is responsible for gathering data from the web.
    It subscribes to TASK_CREATED events and uses Airtop to perform collection.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        super().__init__("CollectionAgent", message_bus, state_store)

    def _handle_collection_task(self, message):
        """Callback to handle the data collection task."""
        try:
            data = json.loads(message['data'])
            task_id = data.get('task_id')
            goal = data.get('goal')
            if not task_id or not goal:
                return
            
            display_event(message['channel'], data, category=self.agent_name, is_incoming=True)
            
            # 1. Update state to COLLECTING
            self.state_store.update_state(task_id, {"status": "COLLECTING"})
            display_status(f"Starting data collection for task '{task_id}'.", category=self.agent_name)
            
            # 2. (TODO) Construct Airtop prompt and invoke the Airtop SDK
            # For now, we'll simulate the process
            display_status("Simulating Airtop data collection... (takes 5s)", category=self.agent_name)
            time.sleep(5) 
            simulated_data_path = f"data/{task_id}_reviews.json"
            # Simulate saving data to a file
            with open(simulated_data_path, 'w') as f:
                json.dump([{"review": "This is a great product!"}], f)
            
            # 3. Update state with the path to the collected data
            self.state_store.update_state(task_id, {
                "status": "COLLECTION_COMPLETE",
                "artifacts": {"raw_data_path": simulated_data_path}
            })
            display_status(f"Data collection finished. Data saved to '{simulated_data_path}'.", category=self.agent_name)

            # 4. Publish COLLECTION_COMPLETE event
            channel = "events:COLLECTION_COMPLETE"
            event_message = {"task_id": task_id, "data_path": simulated_data_path}
            self.message_bus.publish(channel, event_message)
            display_event(channel, event_message, category=self.agent_name)

        except Exception as e:
            display_error(f"Failed during collection for task {task_id}: {e}", agent_id=self.agent_name)
            self.state_store.update_state(task_id, {"status": "COLLECTION_FAILED", "error_log": str(e)})
            # Publish failure event
            channel = "events:COLLECTION_FAILED"
            event_message = {"task_id": task_id, "error": str(e)}
            self.message_bus.publish(channel, event_message)
            display_event(channel, event_message, category=self.agent_name)


    def run(self):
        """Subscribes to TASK_CREATED events and starts the collection process."""
        display_status("Running and waiting for collection tasks.", category=self.agent_name)
        self.message_bus.subscribe("events:TASK_CREATED", self._handle_collection_task)
        self.message_bus.listen()

# No __main__ block needed as this is not intended to be run standalone. 