from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
import time
from typing import Dict, Any

# --- Global Console Object ---
# All rich output should be channeled through this console object.
console = Console()

# --- Core UI Functions ---

def display_header(title="Trendvisor MVP", subtitle="Autonomous Agent-Based E-commerce Analysis Platform"):
    """Displays a standardized, styled header panel."""
    header_text = Text(title, style="bold magenta", justify="center")
    subtitle_text = Text(subtitle, style="bold cyan", justify="center")
    
    panel_content = Text("\n").join([header_text, subtitle_text])
    
    console.print(Panel(
        panel_content,
        expand=False,
        border_style="bold green",
        padding=(1, 10)
    ))
    console.rule("[bold green]System Initializing...[/bold green]")


def display_status(message: str, category: str):
    """Displays a status message with a category label."""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}][{category.upper()}] {message}")


def display_event(channel: str, event_data: Dict[str, Any], category: str, is_incoming: bool = False):
    """Displays an event with its data."""
    direction = "<- RECV" if is_incoming else "-> SENT"
    timestamp = time.strftime('%H:%M:%S')
    task_id = event_data.get('task_id', 'N/A')
    print(f"[{timestamp}][{category.upper()}] {direction} on channel [{channel}] | Task: {task_id}")


def display_final_report(task_id: str, report_path: str):
    """Displays the path to the final report."""
    timestamp = time.strftime('%H:%M:%S')
    print("\n" + "="*80)
    print(f"[{timestamp}][SYSTEM] ✅ TASK COMPLETE: {task_id}")
    print(f"[{timestamp}][SYSTEM] Final report available at: {report_path}")
    print("="*80 + "\n")


def display_error(message: str, agent_id: str = "System"):
    """Displays an error message."""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}][{agent_id.upper()}] ❌ ERROR: {message}")


def display_agent_status(agent_statuses: dict):
    """
    Continuously displays the status of all running agents using a Live display.
    `agent_statuses` should be a dictionary mapping agent_id to its current status message.
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Agent ID", style="dim", width=25)
    table.add_column("Status")

    for agent_id, status in agent_statuses.items():
        table.add_row(f"[magenta]{agent_id}[/magenta]", status)

    return table

if __name__ == '__main__':
    # --- Example Usage for testing the UI components ---
    
    display_header()
    
    time.sleep(1)
    
    display_status("Initializing agent fleet...", category="Orchestrator")
    
    time.sleep(1)
    
    agent_states = {
        "OrchestratorAgent": "Monitoring for new tasks...",
        "CollectionAgent": "Idle, waiting for TASK_CREATED event.",
        "AnalysisAgent": "Idle, waiting for COLLECTION_COMPLETE event."
    }
    
    with Live(display_agent_status(agent_states), refresh_per_second=4) as live:
        time.sleep(2)
        
        agent_states["OrchestratorAgent"] = "New task 'analyze-suntan-lotion' received. Publishing TASK_CREATED."
        live.update(display_agent_status(agent_states))
        time.sleep(1)
        
        display_event("TASK_CREATED", {"task_id": "analyze-suntan-lotion"}, "CollectionAgent")
        
        agent_states["CollectionAgent"] = "Running crawl_reviews tool..."
        agent_states["OrchestratorAgent"] = "Monitoring task 'analyze-suntan-lotion'."
        live.update(display_agent_status(agent_states))
        time.sleep(2)
        
        agent_states["CollectionAgent"] = "Crawl complete. Publishing COLLECTION_COMPLETE."
        live.update(display_agent_status(agent_states))
        time.sleep(1)

        display_event("COLLECTION_COMPLETE", {"task_id": "analyze-suntan-lotion"}, "AnalysisAgent")
        
        agent_states["AnalysisAgent"] = "Running analyze_and_visualize tool..."
        agent_states["CollectionAgent"] = "Idle, waiting for TASK_CREATED event."
        live.update(display_agent_status(agent_states))
        time.sleep(3)
        
        agent_states["AnalysisAgent"] = "Analysis complete. Publishing TASK_COMPLETE."
        live.update(display_agent_status(agent_states))
        time.sleep(1)

    display_status("All agents have completed their tasks.", category="Orchestrator")
    
    console.rule("[bold green]Workflow Finished[/bold green]")
    
    display_final_report("analyze-suntan-lotion", "results/professional_report.html")
    
    display_error("Failed to connect to the LLM endpoint.", agent_id="AnalysisAgent") 