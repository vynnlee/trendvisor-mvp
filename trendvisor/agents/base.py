from abc import ABC, abstractmethod
from typing import Dict, Any
import threading

from trendvisor.core.message_bus import MessageBus
from trendvisor.core.state_store import StateStore
from trendvisor.core.ui import display_status

class BaseAgent(ABC):
    """An abstract base class for all agents in the system."""

    def __init__(self, agent_name: str, message_bus: MessageBus, state_store: StateStore):
        """
        Initializes the agent.
        """
        self.agent_name = agent_name
        self.message_bus = message_bus
        self.state_store = state_store
        self._stop_event = threading.Event()
        self.subscriber_thread = threading.Thread(target=self.run, daemon=True)
        print(f"[{self.agent_name}] Initialized.")

    def start(self):
        """Starts the agent's event subscription thread."""
        display_status(f"Starting...", category=self.agent_name)
        self.subscriber_thread.start()

    def stop(self):
        """Signals the agent's subscription thread to stop."""
        display_status(f"Stopping...", category=self.agent_name)
        self._stop_event.set()
        self.subscriber_thread.join(timeout=2)

    @abstractmethod
    def run(self):
        """
        The main loop for the agent. This method should contain the core logic
        for the agent's operation, such as subscribing to events and processing them.
        """
        pass

    def handle_event(self, event_type: str, payload: Dict[str, Any]):
        """
        The core logic of the agent resides here. This method is called
        by the message bus subscription for each new event. Subclasses must implement this.
        """
        pass 