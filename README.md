# Autonomous Agentic Framework

This project implements a stateful, autonomous agentic framework as described in the System Design Plan.

## Overview

The system is designed to understand user queries, formulate complex plans, execute them as Python scripts, and learn from its interactions. The architecture is built around a primary Execution Agent that interfaces with a powerful set of tools, a persistent memory system, and a sophisticated real-time validation layer.

## Core Components

- **Execution Agent**: The primary reasoning agent that generates Python Action Scripts.
- **Memory Retrieval Agent**: Retrieves relevant long-term memories to provide context.
- **Memory Consolidation Agent**: Creates and stores long-term memories from completed tasks.
- **Action Script Execution Environment**: Executes the generated Python scripts in a controlled environment.
- **Incremental Linter Subsystem**: Provides real-time validation of the Action Script as it's being generated.

## Getting Started

1.  **Set up Environment Variables**:
    Ensure your `GEMINI_API_KEY` is set in the `.env` file.

2.  **Install Dependencies**: 
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**:
    ```bash
    python main.py
    ```
