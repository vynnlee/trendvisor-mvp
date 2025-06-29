import time
from .base import BaseAgent
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_final_report, display_error

class OrchestratorAgent(BaseAgent):
    """
    The master agent that initiates and monitors the overall analysis task.
    It's responsible for starting the workflow and reporting the final outcome.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        # This agent listens for the final completion or failure events.
        super().__init__("OrchestratorAgent", message_bus, state_store, subscribed_events=["TASK_COMPLETE", "TASK_FAILED"])
    
    def handle_event(self, event_type: str, payload: dict):
        """
        Handles the final task outcome events.
        """
        task_id = payload.get("task_id")
        if not task_id:
            return

        display_event(event_type, payload, self.agent_name)
        
        final_state = self.state_store.get_state(task_id)

        if event_type == "TASK_COMPLETE":
            report_path = final_state.get("report_path", "N/A") if final_state else "N/A"
            display_final_report(task_id, report_path)
        
        elif event_type == "TASK_FAILED":
            error_message = final_state.get("error", "An unknown error occurred.") if final_state else "Unknown error."
            failed_by = final_state.get("failed_by", "Unknown Agent") if final_state else "Unknown Agent"
            display_error(error_message, agent_id=failed_by)

        # This is the crucial step: signal the main thread to stop waiting.
        self._stop_event.set()

    def start_new_task(self, product_name: str) -> str:
        """
        Creates a new analysis task and publishes the initial TASK_CREATED event.
        """
        task_id = f"task_{product_name.replace(' ', '_')}_{int(time.time())}"
        initial_state = {
            "task_id": task_id,
            "product_name": product_name,
            "status": "CREATED",
            "history": [f"Task created for {product_name} by {self.agent_name}"]
        }
        self.state_store.set_state(task_id, initial_state)
        display_status(f"New task '{task_id}' created for product '{product_name}'.", category=self.agent_name)
        
        payload = {"task_id": task_id, "product_name": product_name}
        self.message_bus.publish(
            event_type="TASK_CREATED",
            source_agent=self.agent_name,
            payload=payload
        )
        return task_id

    def wait_for_completion(self):
        """
        Waits until the stop event is set by the event handler in this agent.
        This blocks the main application thread, allowing agents to work.
        """
        display_status("Monitoring task workflow... (Press Ctrl+C to exit)", category=self.agent_name)
        # We use the BaseAgent's _stop_event, which will be set by our own handle_event.
        self._stop_event.wait()
        display_status("Workflow finished. Main thread unblocked.", category=self.agent_name)
    
    # Orchestrator doesn't need a custom stop() method anymore, 
    # as the BaseAgent's stop() is now sufficient for shutdown.
    # The wait_for_completion is unblocked by handle_event, not by stop().

if __name__ == '__main__':
    # This is for testing the agent in isolation
    # You would need a running Redis instance for this to work
    try:
        state_store = StateStore()
        message_bus = MessageBus()
        orchestrator = OrchestratorAgent(message_bus, state_store)
        orchestrator.start()
        
        # Simulate creating a task
        task_id = orchestrator.start_new_task("sunscreen")
        print(f"Task {task_id} started.")

        # In a real scenario, other agents would publish these events
        # Here, we simulate them for demonstration
        time.sleep(2)
        print("\n--- Simulating TASK_COMPLETE event ---")
        message_bus.publish(
            event_type="TASK_COMPLETE", 
            source_agent="AnalysisAgent",
            payload={"task_id": task_id, "report_path": "results/simulated_report.html"}
        )
        
        orchestrator.wait_for_completion()
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Orchestrator agent test finished.")
        if 'orchestrator' in locals() and orchestrator.subscriber_thread.is_alive():
            orchestrator.stop()