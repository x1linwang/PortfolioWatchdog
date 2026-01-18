import streamlit as st
import db_manager as db
import asyncio
import os
import sys
import threading
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from streamlit.runtime.scriptrunner import add_script_run_ctx

# --- SETUP ---
db.init_db()
LOCAL_SERVER_PATH = os.path.join(os.path.dirname(__file__), "server.py")
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")

st.set_page_config(page_title="AI Hedge Fund", layout="wide")

# --- AUTHENTICATION ---
if "user" not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    st.title("🔐 Portfolio Login")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login Tab
    with tab1:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Login"):
            if db.login(u, p):
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid credentials")
    
    # Register Tab
    with tab2:
        u2 = st.text_input("New User")
        p2 = st.text_input("New Pass", type="password")
        if st.button("Sign Up"):
            if u2 and p2:
                if db.create_user(u2, p2): 
                    st.success("Created! Please login.")
                else:
                    st.error("Error creating user (User might exist).")
            else:
                st.warning("Please enter both username and password.")

# --- MAIN DASHBOARD ---
else:
    user = st.session_state.user
    
    with st.sidebar:
        st.header(f"👤 {user}")
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
        st.divider()
        if TAVILY_KEY: st.success("🟢 Tavily Research: On")
        else: st.error("🔴 Tavily API Key Missing")

    st.title("Portfolio Watchdog")
    st.caption("Transparent Agent: See the thoughts, tools, and actions below.")

    if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "system",
                "content": f"""
                You are an Autonomous Portfolio Manager for {user}. Your goal is to protect capital and maximize returns.

                ### YOUR TOOLKIT (AND WHEN TO USE THEM):
                
                1. **Market Research (HIERARCHY):**
                - ALWAYS try `investigate_market` (Local News) first. It is faster and focused.
                - ONLY if local news is empty, outdated, or insufficient, use `tavily_news_search` (Web) as a fallback.
                
                2. **Risk Management:**
                - Use `check_portfolio_health` to see holdings and calculating VaR (Value at Risk).
                - Explain risk in simple terms (e.g., "You could lose $500 today").
                
                3. **Trading:**
                - `buy_asset` / `sell_asset`.
                - NEVER trade without first confirming the current price and risk profile.
                
                4. **Communication (CRITICAL):**
                - `send_discord_alert`: Sends a notification to the user's phone.
                
                ### ALERT PROTOCOL (INTELLIGENT NOTIFICATION LOGIC):
                
                You have authority to alert the user even if they didn't explicitly ask, under these conditions:
                - **CRITICAL NEWS:** If you find news about a crash, lawsuit, earnings beat/miss, or major regulatory shift.
                - **HIGH RISK:** If portfolio volatility exceeds safe levels.
                
                If the news is mundane, just summarize it in the chat. If it is URGENT, fire the `send_discord_alert` tool immediately.
                """
            }]

    # --- DISPLAY TOOL CALLS ---
    tool_call_registry = {}
    
    # 1. Index tool calls
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            role = msg["role"]
            content = msg.get("content")
            tool_calls = msg.get("tool_calls", [])
        else:
            role = msg.role
            content = msg.content
            tool_calls = getattr(msg, "tool_calls", [])

        if role == "assistant" and tool_calls:
            for tc in tool_calls:
                tool_call_registry[tc.id] = {
                    "name": tc.function.name,
                    "args": tc.function.arguments
                }

    # 2. Render messages
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            role = msg["role"]
            tool_id = msg.get("tool_call_id")
            content = msg.get("content")
        else:
            role = msg.role
            tool_id = getattr(msg, "tool_call_id", None)
            content = msg.content

        if role == "user":
            with st.chat_message("user"): st.write(content)
        elif role == "assistant" and content:
            with st.chat_message("assistant"): st.write(content)
        elif role == "tool":
            call_info = tool_call_registry.get(tool_id, {"name": "Unknown", "args": "{}"})
            name = call_info["name"]
            args = call_info["args"]
            
            with st.chat_message("assistant", avatar="🛠️"):
                label = f"Executed: `{name}`"
                with st.expander(label, expanded=False):
                    st.markdown("**Parameters:**")
                    st.code(args, language="json")
                    st.markdown("**Output Result:**")
                    st.code(content)

    prompt = st.chat_input("Ex: 'Research stocks in my portfolio and alert me on Discord if needed")

    # --- The core thinking loop ---
    def run_orchestrator(user_prompt):
        async def run_process():
            local_params = StdioServerParameters(command=sys.executable, args=[LOCAL_SERVER_PATH], env=os.environ.copy())
            tavily_params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_tavily"], env=os.environ.copy())

            if not TAVILY_KEY: return

            async with stdio_client(local_params) as (r_loc, w_loc), \
                       stdio_client(tavily_params) as (r_tav, w_tav):
                
                async with ClientSession(r_loc, w_loc) as sess_local, \
                           ClientSession(r_tav, w_tav) as sess_tavily:
                    
                    await sess_local.initialize()
                    await sess_tavily.initialize()

                    tool_map = {}
                    openai_tools = []

                    for sess, label in [(sess_local, "[LOCAL]"), (sess_tavily, "[WEB]")]:
                        tools = await sess.list_tools()
                        for t in tools.tools:
                            tool_map[t.name] = sess
                            openai_tools.append({
                                "type": "function",
                                "function": {"name": t.name, "description": f"{label} {t.description}", "parameters": t.inputSchema}
                            })

                    client = OpenAI()
                    st.session_state.messages.append({"role": "user", "content": user_prompt})
                    with st.chat_message("user"): st.write(user_prompt)

                    with st.chat_message("assistant"):
                        # The AI is allowed to take up to 5 consecutive actions to solve user's problem
                        for _ in range(5):
                            completion = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages, tools=openai_tools)
                            msg = completion.choices[0].message
                            st.session_state.messages.append(msg)

                            if not msg.tool_calls:
                                st.write(msg.content)
                                break
                            
                            for tool in msg.tool_calls:
                                fname = tool.function.name
                                args = eval(tool.function.arguments)
                                target = tool_map[fname]
                                
                                source = "LOCAL" if target == sess_local else "WEB"
                                with st.status(f"🚀 {source}: Calling `{fname}`...", expanded=True):
                                    st.write(f"Input: {args}")
                                    res = await target.call_tool(fname, arguments=args)
                                    output = res.content[0].text
                                    st.write("Done!")
                                    
                                st.session_state.messages.append({
                                    "role": "tool", 
                                    "tool_call_id": tool.id, 
                                    "content": output
                                })

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        t = threading.Thread(target=loop.run_until_complete, args=(run_process(),))
        add_script_run_ctx(t)
        t.start()
        t.join()

    if prompt:
        run_orchestrator(prompt)