import threading
import time
import argparse
import sys
import signal
from trendvisor.core.state_store import StateStore
from trendvisor.core.message_bus import MessageBus
from trendvisor.agents.orchestrator_agent import OrchestratorAgent
from trendvisor.agents.collection_agent import CollectionAgent
from trendvisor.agents.analysis_agent import AnalysisAgent
from trendvisor.core.ui import display_header, display_error, display_status

def run_agent(agent):
    """Function to run an agent's main loop."""
    try:
        agent.run()
    except KeyboardInterrupt:
        display_status(f"{agent.agent_name} received shutdown signal.", category="SYSTEM")

def main():
    """
    Initializes and runs the Trendvisor agent network.
    """
    parser = argparse.ArgumentParser(description="Trendvisor - AI-Powered Market Analysis")
    parser.add_argument("goal", type=str, help="The high-level analysis goal (e.g., 'analyze sunscreen reviews on Olive Young').")
    args = parser.parse_args()

    display_header()

    # --- Graceful Shutdown Handler ---
    def shutdown_handler(signum, frame):
        print("\n") # Newline for cleaner exit
        display_error("Shutdown signal received. Terminating all agents.", "SYSTEM")
        # The 'finally' block will handle the cleanup.
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    display_status("Initializing Trendvisor Agent Network...", category="SYSTEM")
    
    # 1. Initialize core components
    message_bus = MessageBus()
    state_store = StateStore()

    # 2. Initialize agents
    orchestrator = OrchestratorAgent(message_bus, state_store)
    collection_agent = CollectionAgent(message_bus, state_store)
    analysis_agent = AnalysisAgent(message_bus, state_store)

    agents = [orchestrator, collection_agent, analysis_agent]
    threads = []

    # 3. Run each agent in a separate thread
    for agent in agents:
        thread = threading.Thread(target=run_agent, args=(agent,), daemon=True)
        threads.append(thread)
        thread.start()
        display_status(f"{agent.agent_name} is running.", category="SYSTEM")
    
    # Give agents a moment to initialize and subscribe
    time.sleep(1)

    # 4. Start the main task
    try:
        task_id = orchestrator.start_task(args.goal)
        display_status(f"Workflow for task '{task_id}' initiated.", category="SYSTEM")
        
        # Wait for the orchestrator to signal completion of all its tasks
        # In this simple model, we check if the orchestrator's active_tasks list is empty.
        while orchestrator.active_tasks:
            time.sleep(2)

    except KeyboardInterrupt:
        display_status("Shutdown signal received. Exiting.", category="SYSTEM")
    finally:
        display_header("System Shutdown", "Terminating agent fleet...")
        for agent in reversed(agents): # Stop in reverse order
            try:
                agent.stop()
            except Exception as e:
                display_error(f"Error stopping agent {getattr(agent, 'agent_name', 'N/A')}: {e}", "SYSTEM")
        
        print("\nTrendvisor has shut down gracefully.")


if __name__ == "__main__":
    main() 