"""
Capture high-resolution screenshots of AgentLab AI dashboard sections.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent
IMAGES_DIR = ROOT_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser_executable():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def run():
    chrome_path = find_browser_executable()
    if not chrome_path:
        print("ERROR: Neither Chrome nor Edge executable was found.")
        sys.exit(1)

    print(f"Using browser: {chrome_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=chrome_path,
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2  # High-DPI / Retina quality
        )
        page = context.new_page()

        print("Navigating to http://127.0.0.1:8000/ ...")
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 1. Full Dashboard Overview
        print("1. Capturing 01_dashboard_overview.png...")
        page.screenshot(path=str(IMAGES_DIR / "01_dashboard_overview.png"))

        # 2. Left Sidebar: Tools Dashboard & Demos
        print("2. Capturing 02_tools_dashboard_sidebar.png...")
        sidebar = page.locator(".sidebar-panel")
        sidebar.screenshot(path=str(IMAGES_DIR / "02_tools_dashboard_sidebar.png"))

        # 3. Single Tool Execution & Trace (Calculator)
        print("3. Executing Calculator query and capturing 03_agent_execution_trace.png...")
        # Inject realistic demo trace message
        calc_injection_js = """
        const chatContainer = document.getElementById('chat-messages-container');
        // Add user message
        const userRow = document.createElement('div');
        userRow.className = 'message-row user-row';
        userRow.innerHTML = `
          <div class="message-avatar">👤</div>
          <div class="message-content">
            <div class="message-header"><span class="sender-name">You</span><span class="message-timestamp">12:15 PM</span></div>
            <div class="message-body">Calculate 9876 * 543</div>
          </div>
        `;
        chatContainer.appendChild(userRow);

        // Add assistant message with trace
        const assistRow = document.createElement('div');
        assistRow.className = 'message-row assistant-row';
        assistRow.innerHTML = `
          <div class="message-avatar">⚡</div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender-name">AgentLab AI</span>
              <span class="message-timestamp">12:15 PM</span>
              <span class="model-badge" style="padding:1px 6px;font-size:0.68rem;">openai/gpt-oss-120b</span>
            </div>
            <div class="message-body">
              <div class="markdown-output"><p><strong>Result:</strong> 9,876 × 543 = <strong>5,362,668</strong></p></div>
              <div class="trace-card open">
                <div class="trace-header">
                  <div class="trace-title">
                    <span>⚡ Agent Execution Trace</span>
                    <span class="trace-count-pill">1 tool call(s)</span>
                  </div>
                  <span class="trace-chevron">▼</span>
                </div>
                <div class="trace-timeline">
                  <div class="trace-step start">
                    <div class="trace-step-icon">📥</div>
                    <div class="trace-step-body"><div class="trace-step-label">User request received: 'Calculate 9876 * 543'</div></div>
                  </div>
                  <div class="trace-step thought">
                    <div class="trace-step-icon">🧠</div>
                    <div class="trace-step-body"><div class="trace-step-label">Agent analyzed request. 5 tools active in registry.</div></div>
                  </div>
                  <div class="trace-step tool_call">
                    <div class="trace-step-icon">🔧</div>
                    <div class="trace-step-body">
                      <div class="trace-step-label">Tool selected: 'calculator'</div>
                      <div class="trace-step-meta">
                        <span style="color:var(--accent-cyan);">args: {"expression": "9876 * 543"}</span>
                        <button class="btn-inspect-tool" id="btn-demo-inspect">🔍 Inspect</button>
                      </div>
                    </div>
                  </div>
                  <div class="trace-step tool_result">
                    <div class="trace-step-icon">⚙️</div>
                    <div class="trace-step-body">
                      <div class="trace-step-label">Tool 'calculator' executed successfully.</div>
                      <div class="trace-step-meta">
                        <span style="color:var(--accent-green);">Result: 5362668 (2.8ms)</span>
                      </div>
                    </div>
                  </div>
                  <div class="trace-step final_answer">
                    <div class="trace-step-icon">📝</div>
                    <div class="trace-step-body"><div class="trace-step-label">Agent synthesized final response from 1 tool execution.</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
        chatContainer.appendChild(assistRow);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        """
        page.evaluate(calc_injection_js)
        page.wait_for_timeout(500)
        page.screenshot(path=str(IMAGES_DIR / "03_agent_execution_trace.png"))

        # 4. Multi-Tool Orchestration
        print("4. Capturing 04_multi_tool_orchestration.png...")
        multi_tool_js = """
        const chatContainer = document.getElementById('chat-messages-container');
        const userRow = document.createElement('div');
        userRow.className = 'message-row user-row';
        userRow.innerHTML = `
          <div class="message-avatar">👤</div>
          <div class="message-content">
            <div class="message-header"><span class="sender-name">You</span><span class="message-timestamp">12:16 PM</span></div>
            <div class="message-body">Calculate 45 * 72 and tell me the weather in Hyderabad</div>
          </div>
        `;
        chatContainer.appendChild(userRow);

        const assistRow = document.createElement('div');
        assistRow.className = 'message-row assistant-row';
        assistRow.innerHTML = `
          <div class="message-avatar">⚡</div>
          <div class="message-content">
            <div class="message-header">
              <span class="sender-name">AgentLab AI</span>
              <span class="message-timestamp">12:16 PM</span>
              <span class="model-badge" style="padding:1px 6px;font-size:0.68rem;">openai/gpt-oss-120b</span>
            </div>
            <div class="message-body">
              <div class="markdown-output">
                <p><strong>Calculation Result:</strong><br>45 × 72 = <strong>3,240</strong></p>
                <p><strong>Current Weather in Hyderabad, India:</strong></p>
                <ul>
                  <li><strong>Temperature:</strong> 32.7 °C</li>
                  <li><strong>Condition:</strong> Light drizzle</li>
                  <li><strong>Humidity:</strong> 33%</li>
                  <li><strong>Wind Speed:</strong> 9.2 km/h</li>
                </ul>
              </div>
              <div class="trace-card open">
                <div class="trace-header">
                  <div class="trace-title">
                    <span>⚡ Agent Execution Trace</span>
                    <span class="trace-count-pill">2 tool call(s)</span>
                  </div>
                  <span class="trace-chevron">▼</span>
                </div>
                <div class="trace-timeline">
                  <div class="trace-step start">
                    <div class="trace-step-icon">📥</div>
                    <div class="trace-step-body"><div class="trace-step-label">User request received: 'Calculate 45 * 72 and tell me the weather in Hyderabad'</div></div>
                  </div>
                  <div class="trace-step thought">
                    <div class="trace-step-icon">🧠</div>
                    <div class="trace-step-body"><div class="trace-step-label">Agent identified multi-intent request (arithmetic + weather).</div></div>
                  </div>
                  <div class="trace-step tool_call">
                    <div class="trace-step-icon">🔧</div>
                    <div class="trace-step-body">
                      <div class="trace-step-label">Tool 1 selected: 'calculator'</div>
                      <div class="trace-step-meta"><span style="color:var(--accent-cyan);">args: {"expression": "45 * 72"}</span></div>
                    </div>
                  </div>
                  <div class="trace-step tool_result">
                    <div class="trace-step-icon">⚙️</div>
                    <div class="trace-step-body"><div class="trace-step-label">Tool 'calculator' executed successfully (Result: 3240, 1.9ms)</div></div>
                  </div>
                  <div class="trace-step tool_call">
                    <div class="trace-step-icon">🔧</div>
                    <div class="trace-step-body">
                      <div class="trace-step-label">Tool 2 selected: 'weather'</div>
                      <div class="trace-step-meta"><span style="color:var(--accent-cyan);">args: {"location": "Hyderabad"}</span></div>
                    </div>
                  </div>
                  <div class="trace-step tool_result">
                    <div class="trace-step-icon">⚙️</div>
                    <div class="trace-step-body"><div class="trace-step-label">Tool 'weather' executed successfully (Temp: 32.7°C, 184ms)</div></div>
                  </div>
                  <div class="trace-step final_answer">
                    <div class="trace-step-icon">📝</div>
                    <div class="trace-step-body"><div class="trace-step-label">Agent synthesized final response from 2 sequential tool executions.</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
        chatContainer.appendChild(assistRow);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        """
        page.evaluate(multi_tool_js)
        page.wait_for_timeout(500)
        page.screenshot(path=str(IMAGES_DIR / "04_multi_tool_orchestration.png"))

        # 5. Tool Result Inspector Modal
        print("5. Capturing 05_tool_result_inspector_modal.png...")
        modal_open_js = """
        const modal = document.getElementById('inspector-modal');
        const title = document.getElementById('inspector-title');
        const inputPre = document.getElementById('inspector-input');
        const outputPre = document.getElementById('inspector-output');

        title.textContent = '🔧 Inspector: Calculator Execution Payload';
        inputPre.textContent = JSON.stringify({
          "tool": "calculator",
          "arguments": {
            "expression": "9876 * 543"
          }
        }, null, 2);

        outputPre.textContent = JSON.stringify({
          "tool": "calculator",
          "success": true,
          "expression": "9876 * 543",
          "result": 5362668,
          "duration_ms": 2.84
        }, null, 2);

        modal.style.display = 'flex';
        """
        page.evaluate(modal_open_js)
        page.wait_for_timeout(500)
        page.screenshot(path=str(IMAGES_DIR / "05_tool_result_inspector_modal.png"))

        # Close Inspector Modal
        page.evaluate("document.getElementById('inspector-modal').style.display = 'none';")

        # 6. Runtime Settings Drawer
        print("6. Capturing 06_runtime_settings_drawer.png...")
        page.evaluate("document.getElementById('settings-modal').style.display = 'flex';")
        page.wait_for_timeout(500)
        page.screenshot(path=str(IMAGES_DIR / "06_runtime_settings_drawer.png"))

        browser.close()
        print(f"All 6 screenshots successfully captured in {IMAGES_DIR}!")


if __name__ == "__main__":
    run()
