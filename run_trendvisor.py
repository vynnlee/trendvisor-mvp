import sys
import time
import signal
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.agents.orchestrator_agent import OrchestratorAgent
from trendvisor.agents.collection_agent import CollectionAgent
from trendvisor.agents.analysis_agent import AnalysisAgent
from trendvisor.core.ui import display_header, display_error

def main():
    """
    The main entry point for the Trendvisor application.
    Initializes the system, launches agents, and starts a task.
    """
    display_header()

    # --- Graceful Shutdown Handler ---
    def shutdown_handler(signum, frame):
        print("\n") # Newline for cleaner exit
        display_error("Shutdown signal received. Terminating all agents.", "SYSTEM")
        # The 'finally' block will handle the cleanup.
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # --- Argument Check ---
    if len(sys.argv) < 2:
        display_error("You must provide a product name to analyze.", "Usage")
        print("Example: python run_trendvisor.py \"sunscreen for oily skin\"")
        sys.exit(1)
    
    product_name = sys.argv[1]
    
    agents = []
    try:
        # --- Initialization ---
        state_store = StateStore()
        message_bus = MessageBus()
        
        orchestrator = OrchestratorAgent(message_bus, state_store)
        collection_agent = CollectionAgent(message_bus, state_store)
        analysis_agent = AnalysisAgent(message_bus, state_store)
        
        agents = [orchestrator, collection_agent, analysis_agent]

        # --- Agent Fleet Launch ---
        for agent in agents:
            agent.start()
        
        # Give agents a moment to initialize their subscriptions
        time.sleep(1)

        # --- Task Execution ---
        orchestrator.start_new_task(product_name)
        
        # --- Wait for Completion ---
        # The orchestrator will set its stop_event when the task is complete or fails.
        orchestrator.wait_for_completion()

    except Exception as e:
        display_error(f"A critical error occurred: {e}", "SYSTEM")
    
    finally:
        # --- System Shutdown ---
        display_header("System Shutdown", "Terminating agent fleet...")
        for agent in reversed(agents): # Stop in reverse order
            try:
                agent.stop()
            except Exception as e:
                display_error(f"Error stopping agent {getattr(agent, 'agent_name', 'N/A')}: {e}", "SYSTEM")
        
        print("\nTrendvisor has shut down gracefully.")


if __name__ == "__main__":
    main() 