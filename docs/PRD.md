# Trendvisor MVP - Product Requirements Document (PRD)

**Version:** 2.0  
**Status:** In Development  
**Date:** June 29, 2024

---

### 1. Introduction

#### 1.1. Vision
To build a world-class, autonomous AI agent system that provides actionable B2B market insights from unstructured e-commerce data. Trendvisor aims to replace manual market research with a scalable, real-time, and deeply analytical platform.

#### 1.2. Goal for This Phase (Project "Phoenix")
The primary goal of this development phase is to refactor the existing prototype into a robust, scalable, event-driven agent architecture as defined in `ARCHITECTURE.md` (v2.0). This involves not only restructuring internal components but also strategically integrating **best-in-class external services like Airtop** to delegate complex, high-maintenance tasks like web data collection. This foundation will ensure system stability, dramatically reduce maintenance overhead, and accelerate future feature development.

#### 1.3. Target Audience
-   **Primary:** Product Managers, Brand Managers at consumer goods companies.
-   **Secondary:** Data Analysts, Market Researchers.

---

### 2. Key Features & User Stories

#### Epic 1: Autonomous End-to-End Analysis Workflow

> As a user, I want to provide a high-level goal and receive a comprehensive analysis report without any manual intervention, so that I can focus on interpreting results rather than managing processes.

-   **Story 1.1:** As a user, I can initiate an analysis task by providing a simple text-based goal (e.g., "Analyze sunscreen reviews from Olive Young") via a single command-line entry point (`run_trendvisor.py`).
-   **Story 1.2:** As the system, upon receiving a goal, I will autonomously trigger the data collection, analysis, and visualization agents in sequence through the event-driven architecture.
-   **Story 1.3:** As a user, I can observe the real-time status of my task (`COLLECTING`, `ANALYZING`, `COMPLETE`, `FAILED`) through clear CLI logging from the Orchestrator Agent.
-   **Story 1.4:** As the system, upon successful completion, I will store the final HTML report in the `/results` directory with a predictable file name.

#### Epic 2: Core Agent & Tool Capabilities

> As an agent, I need a set of reliable tools to perform my specialized tasks, ensuring the final output meets the quality standards of the previous prototype.

-   **Story 2.1 (Data Collection):** The `collection_agent` must leverage the **Airtop platform** via its Python SDK to reliably scrape reviews. This strategic decision replaces the fragile, script-based `crawl_reviews.py` tool, ensuring higher data integrity and near-zero maintenance for website UI changes.
-   **Story 2.2 (Data Analysis & Visualization):** The `analysis_visualization_agent` must use the `analyze_and_visualize.py` tool to perform all previously implemented analyses and generate a single, comprehensive HTML report.
-   **Story 2.3 (Tool Standardization):** All *local* tools (like `analyze_and_visualize.py`) must accept standardized command-line arguments to be invoked reliably by their respective agents.

#### Epic 3: System Resilience & Observability

> As a developer, I need to easily debug the system and understand its inner workings, and the system must be resilient to common failures.

-   **Story 3.1 (State Management):** The system must use a Redis-based Shared State Store to track the status, metadata, and artifact locations for every task.
-   **Story 3.2 (Observability):** All inter-agent communication must happen through a Redis Pub/Sub Message Bus. A developer should be able to monitor the event channel to trace the entire workflow.
-   **Story 3.3 (Failure Handling):** If a tool or agent fails (e.g., crawler is blocked), it must report a `FAILED` event and log the error to the Shared State Store. The system should stop the workflow for that task gracefully, not crash entirely.

---

### 3. Non-Functional Requirements

-   **Architecture:** Must strictly adhere to the Event-Driven Collaborative Agent Network design specified in `docs/ARCHITECTURE.md` (v2.0).
-   **Performance:** A standard analysis run on ~1000 reviews should be completed within 5 minutes.
-   **Technology Stack:**
    -   Language: Python 3.9+
    -   Infrastructure: Redis (for both Message Bus and State Store).
    -   Key Libraries: `redis-py`, `pandas`, `scikit-learn`, `plotly`, `airtop-sdk`.
-   **External Dependencies:** The system now has a critical dependency on the Airtop API for data collection.
-   **Code Quality:** All code must be packaged within the `trendvisor` module. Agents and tools must be clearly separated.

---

### 4. Success Metrics

-   **Primary Metric:** Successful, unattended, end-to-end execution of at least three different analysis goals (e.g., "sunscreen", "face masks", "vitamin c serum").
-   **Resilience Test:** Manually terminating an agent process mid-workflow correctly results in a `FAILED` task status without crashing the other agents.
-   **Code Review:** The final code structure must perfectly match the design in the updated architecture document.

---

### 5. Out of Scope (For Project Phoenix)

The following items are explicitly out of scope for this refactoring phase and will be considered for future versions:
-   A web-based user interface or dashboard.
-   A persistent database for storing results long-term (e.g., PostgreSQL).
-   Advanced Human-in-the-Loop interactions (e.g., email notifications, approval steps).
-   Dynamic, LLM-based planning and tool selection by the Orchestrator (beyond generating the initial Airtop prompt).
-   Polyglot agent implementations.
-   Horizontal scaling and deployment on cloud infrastructure (e.g., Kubernetes). 