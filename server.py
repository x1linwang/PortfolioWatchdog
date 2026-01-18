from mcp.server.fastmcp import FastMCP
from news_engine import NewsEngine
from finance_tools import FinanceTools
import db_manager as db
import requests
import os

# --- CONFIGURATION ---
# INSTRUCTOR: Paste the Discord Webhook URL here.
# Guide: Discord Server -> Edit Channel -> Integrations -> Webhooks -> New Webhook
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461161966105264160/bMS5X2IOc84YAIHptY7H1ZvKuJyjdYGzZZ-5d8SCfOuL6Mnb0pFny8MQKs2dPFCY3K_S"

mcp = FastMCP("Portfolio Watchdog")
news_db = NewsEngine()

@mcp.tool()
def investigate_market(topic: str) -> str:
    """Scrapes AP News for a topic."""
    return news_db.fetch_ap_news(topic)

@mcp.tool()
def check_portfolio_health(username: str) -> str:
    """
    Analyzes TOTAL portfolio risk. 
    Returns Total Value, Portfolio VaR (Risk), and Weighted Volatility.
    """
    holdings = db.get_portfolio(username) 
    if not holdings: return "Portfolio is empty."

    # Call the new aggregate function
    metrics = FinanceTools.calculate_portfolio_risk(holdings)
    
    # Format a nice report for the LLM
    report = [
        f"📊 **PORTFOLIO REPORT for {username}**",
        f"💰 Total Value: ${metrics['total_value']}",
        f"⚠️ Portfolio Risk (VaR 95%): ${metrics['portfolio_var_usd']} (Potential daily loss)",
        f"📉 Weighted Volatility: {metrics['portfolio_volatility']}%",
        "\n**Holdings Breakdown:**"
    ]
    
    for item in metrics['holdings_summary']:
        report.append(f"- {item['ticker']}: ${item['position_value']} (Risk: ${item['var_95_usd']})")

    return "\n".join(report)

@mcp.tool()
def buy_asset(username: str, ticker: str, shares: float) -> str:
    """Buys a stock (Long position)."""
    db.add_transaction(username, ticker, shares)
    return f"✅ BOUGHT: {shares} of {ticker}."

@mcp.tool()
def sell_asset(username: str, ticker: str, shares: float) -> str:
    """Sells a stock (Reduces position)."""
    db.add_transaction(username, ticker, -shares)
    return f"📉 SOLD: {shares} of {ticker}."

@mcp.tool()
def send_discord_alert(subject: str, message: str) -> str:
    """
    Sends a real notification to the user's Discord channel.
    Use this for urgent alerts, daily reports, or when user asks to 'send this'.
    """
    if "YOUR_WEBHOOK_HERE" in DISCORD_WEBHOOK_URL:
        return "❌ Error: Discord Webhook URL not configured in server.py"

    data = {
        "content": f"🚨 **AGENT ALERT: {subject}**\n\n{message}"
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        if response.status_code == 204:
            return "✅ Notification sent to Discord successfully."
        else:
            return f"❌ Discord Error: {response.status_code}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

if __name__ == "__main__":
    mcp.run()