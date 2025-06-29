import subprocess
import os
from .base import BaseAgent
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_error

class AnalysisAgent(BaseAgent):
    """
    This agent is responsible for analyzing the collected data.
    It listens for COLLECTION_COMPLETE events and runs the analysis tool.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        super().__init__("AnalysisAgent", message_bus, state_store, subscribed_events=["COLLECTION_COMPLETE"])

    def handle_event(self, event_type: str, payload: dict):
        """Handles a COLLECTION_COMPLETE event by running the analysis tool."""
        task_id = payload.get("task_id")
        data_path = payload.get("data_path")

        if not task_id or not data_path:
            display_error(f"Invalid payload for {event_type}: {payload}", self.agent_name)
            return
        
        display_event(event_type, payload, self.agent_name)
        
        try:
            display_status(f"Starting analysis on data: '{data_path}'.", category=self.agent_name)
            self.state_store.update_state(task_id, {"status": "ANALYZING", "analyzer_agent": self.agent_name})

            script_path = os.path.join(os.path.dirname(__file__), '..', 'tools', 'analyze_and_visualize.py')
            result = subprocess.run(
                ["python3", script_path, data_path, task_id],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            
            report_file_path = result.stdout.strip()

            display_status(f"Analysis successful. Report at: '{report_file_path}'.", category=self.agent_name)
            
            self.state_store.update_state(task_id, {"status": "ANALYSIS_COMPLETE", "report_path": report_file_path})
            
            new_payload = {"task_id": task_id, "report_path": report_file_path}
            self.message_bus.publish("TASK_COMPLETE", self.agent_name, new_payload)

        except subprocess.CalledProcessError as e:
            error_message = f"Analysis script failed.\nStderr: {e.stderr.strip()}"
            display_error(error_message, agent_id=self.agent_name)
            self.state_store.update_state(task_id, {"status": "ANALYSIS_FAILED", "error": error_message, "failed_by": self.agent_name})
            self.message_bus.publish("TASK_FAILED", self.agent_name, {"task_id": task_id, "error": error_message})
        
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"
            display_error(error_message, agent_id=self.agent_name)
            self.state_store.update_state(task_id, {"status": "ANALYSIS_FAILED", "error": error_message, "failed_by": self.agent_name})
            self.message_bus.publish("TASK_FAILED", self.agent_name, {"task_id": task_id, "error": error_message}) 