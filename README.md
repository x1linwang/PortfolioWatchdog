# Portfolio Watchdog

This is a functional AI Agent built using the **Model Context Protocol (MCP)**. 
It simulates a Portfolio Manager that can research news, calculate financial risk (VaR), trade stocks, and send alerts to a real Discord channel: https://discord.gg/rQ5rv9Gx.

## 🏗️ System Architecture

This application demonstrates how **LLMs (Large Language Models)** act as "brains" that control distinct software modules.

### 1. The Brain (`app.py` + OpenAI)
- This is the Frontend (Streamlit).
- It holds the **"System Prompt"** which gives the AI its personality and instructions.
- It doesn't know how to trade or calculate math. It only knows how to *ask for help* by selecting tools.

### 2. The Tool Server (`server.py`)
- Built with `FastMCP`.
- This acts as the "Arms and Legs" of the AI.
- It contains the specific Python functions the AI can call:
  - `buy_asset()`: Writes to the database.
  - `check_portfolio_health()`: Runs the math.
  - `send_discord_alert()`: Connects to the internet to send messages.

### 3. The Math Engine (`finance_tools.py`)
- A pure Python library (no AI here).
- It calculates **Value at Risk (VaR)** and **Volatility** using `numpy` and `yfinance`.
- *Lesson:* We use code for math, not the LLM, to ensure accuracy.

### 4. The Database (`db_manager.py`)
- A simple SQLite file (`portfolio.db`) that acts as the "Memory".
- It persists user login info and stock holdings.

---

## How to Run

### Prerequisites
1. **OpenAI API Key:** `export OPENAI_API_KEY="sk-..."`
2. **Tavily API Key (Optional):** `export TAVILY_API_KEY="tvly-..."` (For web search)
3. **Discord Webhook (Optional):** Update `DISCORD_WEBHOOK_URL` in `server.py` to receive real alerts.

### Installation
```bash
pip install -r requirements.txt