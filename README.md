# Project Setup

This document describes how to set up and run the project.

## Prerequisites

*   Python 3.13

## Setup Steps

1.  **Create a virtual environment:**
    ```bash
    python3.13 -m venv .venv
    ```

2.  **Activate the virtual environment:**

    *   On Linux/macOS:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Set up environment variables:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Then, open the `.env` file and add your API key:
    ```
    # .env
    OPENAI_API_KEY=YOUR_API_KEY_HERE
    ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Install pre-commit hooks:**
    ```bash
    python -m pre_commit install
    ```

6.  **Run the program:**
    ```bash
    python main.py
    ```
