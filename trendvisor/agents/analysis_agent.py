import time
import json
import subprocess
import os
from .base import BaseAgent
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.core.ui import display_status, display_event, display_error

class AnalysisAgent(BaseAgent):
    """
    The AnalysisAgent is responsible for running data analysis and visualization.
    It subscribes to COLLECTION_COMPLETE events.
    """
    def __init__(self, message_bus: MessageBus, state_store: StateStore):
        super().__init__("AnalysisAgent", message_bus, state_store)

    def _handle_analysis_task(self, message):
        """Callback to handle the analysis and visualization task."""
        task_id = None # Initialize task_id to ensure it's available for error logging
        try:
            data = json.loads(message['data'])
            task_id = data.get('task_id')
            data_path = data.get('data_path')
            if not task_id or not data_path:
                return
            
            display_event(message['channel'], data, category=self.agent_name, is_incoming=True)
            
            # 1. Update state to ANALYZING
            self.state_store.update_state(task_id, {"status": "ANALYZING"})
            display_status(f"Starting analysis for task '{task_id}'.", category=self.agent_name)
            
            # 2. Run the external analysis tool
            tool_path = os.path.abspath(os.path.join(__file__, '..', '..', 'tools', 'analyze_and_visualize.py'))
            process = subprocess.run(
                ['python3', tool_path, '--input', data_path, '--task_id', task_id],
                capture_output=True, text=True, check=True
            )
            
            report_path = process.stdout.strip()
            display_status(f"Analysis tool finished. Report at: {report_path}", category=self.agent_name)

            # 3. Update state with the report path
            current_state = self.state_store.get_state(task_id)
            if current_state:
                current_state.artifacts['report_path'] = report_path
                current_state.status = "ANALYSIS_COMPLETE"
                self.state_store.save_state(current_state)

            # 4. Publish TASK_COMPLETE event
            channel = "events:TASK_COMPLETE"
            event_message = {"task_id": task_id, "report_path": report_path}
            self.message_bus.publish(channel, event_message)
            display_event(channel, event_message, category=self.agent_name)

        except subprocess.CalledProcessError as e:
            error_msg = f"Analysis tool failed for task {task_id}: {e.stderr}"
            display_error(error_msg, agent_id=self.agent_name)
            if task_id:
                self.state_store.update_state(task_id, {"status": "ANALYSIS_FAILED", "error_log": error_msg})
                # Publish failure event
                channel = "events:TASK_FAILED"
                event_message = {"task_id": task_id, "error": error_msg}
                self.message_bus.publish(channel, event_message)
                display_event(channel, event_message, category=self.agent_name)

    def run(self):
        """Subscribes to COLLECTION_COMPLETE events and starts the analysis process."""
        display_status("Running and waiting for analysis tasks.", category=self.agent_name)
        self.message_bus.subscribe("events:COLLECTION_COMPLETE", self._handle_analysis_task)
        self.message_bus.listen() 