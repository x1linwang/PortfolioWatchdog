# Portfolio Watchdog

<p align="center">
<img src="https://github.com/x1linwang/img/blob/main/logo_final.png?raw=true" alt="Portfolio Watchdog Logo" width="60%"/>
</p>

Welcome to the **Portfolio Watchdog**. This is a fully autonomous Financial Agent capable of researching market news, calculating complex risk metrics (Value at Risk), managing a portfolio, and sending real-time alerts to your phone via Discord.

This project demonstrates the **Model Context Protocol (MCP)** architecture, where a Large Language Model (The Brain) directs independent software tools (The Body) to perform actions in the real world.

---

## System Architecture

<p align="center">
<img src="https://raw.githubusercontent.com/x1linwang/img/d6b46839791721e0d2a5e1b9614f99d7df6c9683/diagram.svg" alt="System Architecture Diagram" width="100%"/>
</p>

To understand how this agent works, visualize three distinct layers:

1.  **The Brain (`app.py` + OpenAI)**
    * **Role:** The decision maker.
    * **Function:** It holds the "System Prompt" (Personality & Rules). It decides *which* tool to use based on your request. It does **not** do math or access the internet directly; it asks tools to do it.
    * **Logic:** It uses a "Reasoning Loop" (Orchestrator) to chain multiple thoughts together (e.g., Search News -> Analyze Risk -> Sell Stock).

2.  **The Body (`server.py`)**
    * **Role:** The tool executor (MCP Server).
    * **Function:** Contains the Python functions that actually *do* the work:
        * `buy_asset()`: Writes to the database.
        * `check_portfolio_health()`: Calculates math.
        * `send_discord_alert()`: Sends data to the outside world.

3.  **The Tool Box**
    * **`finance_tools.py`**: A pure Python math library for calculating Volatility and VaR.
    * **`news_engine.py`**: A scraper for local AP News data.
    * **`db_manager.py`**: A SQLite database (`portfolio.db`) acting as the agent's long-term memory.

---

## Setup Guide

### 1. Prerequisites
You need **Python 3.10+** installed.

### 2. Installation
Clone the repository (or download the folder) and install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. API Keys Configuration
This agent requires two "Keys" to function. You must set these in your terminal environment before running the app.

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-proj-..."
export TAVILY_API_KEY="tvly-..."
```

**Windows (Powershell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-..."
$env:TAVILY_API_KEY="tvly-..."
```

* **OpenAI Key:** Required for the "Brain" (GPT-4o). Get one at [openai.com](https://openai.com/api/).
* **Tavily Key:** Required for the "Web Search" tool. Get one for free at [tavily.com](https://tavily.com).

---

## Discord Alert Setup (Crucial Step)

To test the **Real-time Alert System**, you need to give the Agent a destination to send messages to. We use **Discord Webhooks** for this.

**Instructions:**

1.  **Create a Testing Server:** Open Discord, click the `+` on the left sidebar, and "Create My Own" server. Call it "Hedge Fund Bot Test".
2.  **Create a Channel:** Make a text channel named `#alerts`.
3.  **Get the Webhook URL:**
    * Click the **Gear Icon ⚙️** next to the channel name (`Edit Channel`).
    * Go to **Integrations** > **Webhooks**.
    * Click **New Webhook**.
    * Name it "Agent Smith" (or whatever you want).
    * Click **Copy Webhook URL**.
4.  **Configure the Webhook:**
**Mac/Linux:**
```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

**Windows (Powershell):**
```powershell
$env:DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

*Note: Do not share this URL publicly, or anyone can post messages to your channel.*

---

## How to Run

Once your keys are set and your Webhook is pasted:

```bash
streamlit run app.py
```

1.  **Login/Register:** Create a dummy account (e.g., User: `admin`, Pass: `1234`).
2.  **Start Trading:** Use the chat interface to command your agent.

---

## Experiments to Try

The Agent has "Intelligent Logic" built into its prompt. Try these scenarios to see it in action:

### Experiment 1: The "Smart" Search
* **Prompt:** *"What is happening with Apple stock right now?"*
* **Observation:** Open the "Thoughts" expander.
    * It will first try `investigate_market` (Local News).
    * If that fails, it will switch to `tavily_news_search` (Web Search).
    * This demonstrates **Hierarchical Tool Use**.

### Experiment 2: The "Proactive" Alert
* **Prompt:** *"Find me a stock that is crashing right now and tell me why."*
* **Observation:**
    * If the news is "Critical" (e.g., a crash or scandal), the Agent is programmed to **automatically** fire the `send_discord_alert` tool.
    * Check your Discord channel—you should see the notification pop up instantly.

### Experiment 3: Risk Management
* **Prompt:** *"Buy 100 shares of TSLA."*
* **Prompt:** *"Analyze my portfolio health."*
* **Observation:**
    * The Agent will calculate the **Value at Risk (VaR)**.
    * It will tell you how much money you could potentially lose on a bad day (e.g., *"Portfolio Risk: $450.00"*).

---

## File Structure

* `app.py`: The User Interface and System Prompt.
* `server.py`: The MCP Server containing the tools.
* `finance_tools.py`: The math logic for Volatility/VaR.
* `news_engine.py`: The web scraper.
* `db_manager.py`: Database handler.
* `portfolio.db`: The file where your trades are saved (created automatically).