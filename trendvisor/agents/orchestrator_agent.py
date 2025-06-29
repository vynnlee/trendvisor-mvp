import time
import json
from .base import BaseAgent
from trendvisor.core.state_store import StateStore, TaskState
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_final_report, display_error

class OrchestratorAgent(BaseAgent):
    """
    The OrchestratorAgent is responsible for initiating tasks and monitoring their
    overall progress. It acts as the entry point for user requests.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        super().__init__("OrchestratorAgent", message_bus, state_store)
        self.active_tasks = {}
    
    def start_task(self, goal: str) -> str:
        """
        Initiates a new analysis task from a user-defined goal.
        """
        task_id = f"task_{goal.split(' ')[0].lower()}_{int(time.time())}"
        display_status(f"New task received. Goal: '{goal}'.", category=self.agent_name)

        # 1. Create and save the initial state using the Pydantic model
        initial_state = TaskState(task_id=task_id, goal=goal, status="CREATED")
        self.state_store.save_state(initial_state)
        display_status(f"Initial state for task '{task_id}' saved.", category=self.agent_name)

        # 2. Publish the TASK_CREATED event
        channel = "events:TASK_CREATED"
        event_message = {
            "task_id": task_id,
            "goal": goal,
        }
        self.message_bus.publish(channel, event_message)
        display_event(channel, event_message, category=self.agent_name)
        
        self.active_tasks[task_id] = "RUNNING"
        return task_id

    def _handle_final_events(self, message):
        """Callback for handling terminal events like TASK_COMPLETE or TASK_FAILED."""
        try:
            channel = message['channel']
            event_type = channel.split(':')[-1]
            data = json.loads(message['data'])
            task_id = data.get('task_id')

            if not task_id or task_id not in self.active_tasks:
                return

            display_event(channel, data, category=self.agent_name, is_incoming=True)
            
            final_state = self.state_store.get_state(task_id)
            if not final_state:
                display_error(f"Could not retrieve final state for task {task_id}", agent_id=self.agent_name)
                return

            if event_type == "TASK_COMPLETE":
                report_path = final_state.artifacts.get('report_path', 'N/A')
                display_final_report(task_id, report_path)
            elif event_type == "TASK_FAILED":
                display_error(f"Task '{task_id}' failed. Reason: {final_state.error_log}", agent_id=self.agent_name)
            
            self.active_tasks.pop(task_id, None)

        except (json.JSONDecodeError, KeyError) as e:
            display_error(f"Could not process final event: {message}. Error: {e}", agent_id=self.agent_name)

    def run(self):
        """
        The orchestrator subscribes to final status events to monitor outcomes.
        """
        display_status("Running and monitoring task outcomes.", category=self.agent_name)
        
        # Subscribe to terminal events
        self.message_bus.subscribe("events:TASK_COMPLETE", self._handle_final_events)
        self.message_bus.subscribe("events:TASK_FAILED", self._handle_final_events)
        
        # Start listening in a non-blocking way
        listener_thread = self.message_bus.listen()
        
        # Keep the agent alive while tasks are running or until stopped
        while self.active_tasks:
            time.sleep(1)
        
        display_status("All tasks completed. Stopping listener.", category=self.agent_name)
        if listener_thread and listener_thread.is_alive():
            listener_thread.stop()

if __name__ == '__main__':
    # This is for testing the agent in isolation
    # You would need a running Redis instance for this to work
    try:
        state_store = StateStore()
        message_bus = MessageBus()
        orchestrator = OrchestratorAgent(message_bus, state_store)
        
        # Run orchestrator in a separate thread to not block the main thread
        import threading
        orchestrator_thread = threading.Thread(target=orchestrator.run, daemon=True)
        orchestrator_thread.start()

        # Simulate creating a task
        task_id = orchestrator.start_task("analyze sunscreen reviews")
        print(f"Main thread: Task {task_id} started.")

        # In a real run, other agents would publish these events.
        # For this test, we simulate them.
        time.sleep(2)
        print("\nMain thread: Simulating a TASK_COMPLETE event...")
        message_bus.publish("events:TASK_COMPLETE", {
            "task_id": task_id,
            "report_path": "/results/simulated_report.html"
        })

        # Give the orchestrator time to process the event
        time.sleep(2)
        print("Main thread: Test finished.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Orchestrator agent test finished.")
        if 'orchestrator' in locals() and orchestrator.subscriber_thread.is_alive():
            orchestrator.stop()