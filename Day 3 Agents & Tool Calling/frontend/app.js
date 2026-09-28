/**
 * AgentLab AI - Frontend Client Controller
 * Manages chat interactions, execution traces, tool toggles, and modal inspectors.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    enabledTools: ['calculator', 'search', 'weather', 'database', 'custom'],
    conversationHistory: [],
    settings: {
      model: 'openai/gpt-oss-120b',
      temperature: 0.2,
      maxToolCalls: 5,
    },
    toolsRegistry: {},
    isGenerating: false,
  };

  // DOM Elements
  const chatMessagesContainer = document.getElementById('chat-messages-container');
  const chatForm = document.getElementById('chat-form');
  const userInputField = document.getElementById('user-input-field');
  const btnSubmit = document.getElementById('btn-submit');
  const btnClearChat = document.getElementById('btn-clear-chat');
  const providerStatusText = document.getElementById('provider-status-text');
  const modelNameText = document.getElementById('model-name-text');
  const toolsActiveBadge = document.getElementById('tools-active-badge');
  const inputToolsSummary = document.getElementById('input-tools-summary');

  // Modals & Drawers
  const btnSettingsToggle = document.getElementById('btn-settings-toggle');
  const settingsModal = document.getElementById('settings-modal');
  const btnCloseSettings = document.getElementById('btn-close-settings');
  const btnSaveSettings = document.getElementById('btn-save-settings');
  const settingModel = document.getElementById('setting-model');
  const settingTemperature = document.getElementById('setting-temperature');
  const valTemperature = document.getElementById('val-temperature');
  const settingMaxTools = document.getElementById('setting-max-tools');
  const valMaxTools = document.getElementById('val-max-tools');

  // Tool Inspector
  const inspectorModal = document.getElementById('inspector-modal');
  const inspectorTitle = document.getElementById('inspector-title');
  const inspectorInput = document.getElementById('inspector-input');
  const inspectorOutput = document.getElementById('inspector-output');
  const btnCloseInspector = document.getElementById('btn-close-inspector');
  const btnCloseInspectorAction = document.getElementById('btn-close-inspector-action');
  const btnCopyInspector = document.getElementById('btn-copy-inspector');

  let currentInspectorData = null;

  // Initialize Application
  async function init() {
    setupEventListeners();
    await checkHealth();
    await loadToolsMetadata();
    updateToolsBadge();
  }

  // Health Check
  async function checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        providerStatusText.textContent = `${data.provider.toUpperCase()} (${data.status})`;
        modelNameText.textContent = data.default_model;
        state.settings.model = data.default_model;
        settingModel.value = data.default_model;
      } else {
        providerStatusText.textContent = 'API Offline';
      }
    } catch (err) {
      providerStatusText.textContent = 'Server Disconnected';
    }
  }

  // Load Tool Schemas from Backend
  async function loadToolsMetadata() {
    try {
      const res = await fetch('/api/tools');
      if (res.ok) {
        const data = await res.json();
        data.tools.forEach((t) => {
          state.toolsRegistry[t.name] = t;
        });
      }
    } catch (err) {
      console.error('Failed to load tool schemas', err);
    }
  }

  // Update Enabled Tools List
  function updateEnabledTools() {
    const checkboxes = document.querySelectorAll('.tool-checkbox');
    state.enabledTools = [];
    checkboxes.forEach((cb) => {
      if (cb.checked) {
        state.enabledTools.push(cb.getAttribute('data-tool'));
      }
    });
    updateToolsBadge();
  }

  function updateToolsBadge() {
    const total = 5;
    const active = state.enabledTools.length;
    toolsActiveBadge.textContent = `${active}/${total} Active`;

    // Update input summary pills
    inputToolsSummary.innerHTML = '<span class="tiny-label">Active:</span>';
    state.enabledTools.forEach((t) => {
      const pill = document.createElement('span');
      pill.className = 'tool-tag-pill';
      pill.textContent = t.charAt(0).toUpperCase() + t.slice(1);
      inputToolsSummary.appendChild(pill);
    });
  }

  // Send Message Routine
  async function handleSendMessage(text) {
    const query = (text || userInputField.value).trim();
    if (!query || state.isGenerating) return;

    // Reset input
    userInputField.value = '';
    userInputField.style.height = 'auto';

    // Append user row
    appendUserMessage(query);

    // Append loading assistant row
    const loadingRowId = `loading-${Date.now()}`;
    appendLoadingMessage(loadingRowId);
    scrollToBottom();

    state.isGenerating = true;
    btnSubmit.disabled = true;

    try {
      const payload = {
        message: query,
        enabled_tools: state.enabledTools,
        model: state.settings.model,
        temperature: state.settings.temperature,
        max_tool_calls: state.settings.maxToolCalls,
        conversation_history: state.conversationHistory.slice(-4),
      };

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      removeLoadingMessage(loadingRowId);

      if (response.ok && data.success) {
        appendAssistantMessage(data);
        // Save history
        state.conversationHistory.push({ role: 'user', content: query });
        state.conversationHistory.push({ role: 'assistant', content: data.answer });
      } else {
        appendErrorMessage(data.detail || data.error || data.answer || 'An error occurred during agent execution.');
      }
    } catch (err) {
      removeLoadingMessage(loadingRowId);
      appendErrorMessage(`Network or connection failure: ${err.message}`);
    } finally {
      state.isGenerating = false;
      btnSubmit.disabled = false;
      scrollToBottom();
    }
  }

  // Append User Message to UI
  function appendUserMessage(text) {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const row = document.createElement('div');
    row.className = 'message-row user-row';
    row.innerHTML = `
      <div class="message-avatar">👤</div>
      <div class="message-content">
        <div class="message-header">
          <span class="sender-name">You</span>
          <span class="message-timestamp">${time}</span>
        </div>
        <div class="message-body">
          ${escapeHtml(text)}
        </div>
      </div>
    `;
    chatMessagesContainer.appendChild(row);
  }

  // Append Loading Row
  function appendLoadingMessage(id) {
    const row = document.createElement('div');
    row.className = 'message-row assistant-row';
    row.id = id;
    row.innerHTML = `
      <div class="message-avatar">⚡</div>
      <div class="message-content">
        <div class="message-header">
          <span class="sender-name">AgentLab AI</span>
          <span class="message-timestamp">Reasoning...</span>
        </div>
        <div class="message-body">
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="spinner"></div>
            <span style="font-size:0.85rem;color:var(--text-secondary);">Analyzing intent and selecting tools...</span>
          </div>
        </div>
      </div>
    `;
    chatMessagesContainer.appendChild(row);
  }

  function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  // Append Assistant Message with Execution Trace
  function appendAssistantMessage(data) {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const row = document.createElement('div');
    row.className = 'message-row assistant-row';

    // Parse Markdown safely
    const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(data.answer) : escapeHtml(data.answer);

    // Build Execution Trace Widget
    const traceHtml = buildTraceWidget(data.trace, data.tool_calls_executed);

    row.innerHTML = `
      <div class="message-avatar">⚡</div>
      <div class="message-content">
        <div class="message-header">
          <span class="sender-name">AgentLab AI</span>
          <span class="message-timestamp">${time}</span>
          <span class="model-badge" style="padding:1px 6px;font-size:0.68rem;">${data.model_used}</span>
        </div>
        <div class="message-body">
          <div class="markdown-output">${parsedMarkdown}</div>
          ${traceHtml}
        </div>
      </div>
    `;

    chatMessagesContainer.appendChild(row);

    // Attach inspect click handlers for this message
    row.querySelectorAll('.btn-inspect-tool').forEach((btn) => {
      btn.addEventListener('click', () => {
        const stepIndex = parseInt(btn.getAttribute('data-step-index'), 10);
        const traceItem = data.trace.find((t) => t.step === stepIndex);
        if (traceItem) {
          openInspector(traceItem);
        }
      });
    });

    // Attach trace accordion toggle
    const traceHeader = row.querySelector('.trace-header');
    if (traceHeader) {
      traceHeader.addEventListener('click', () => {
        const card = traceHeader.closest('.trace-card');
        card.classList.toggle('open');
      });
    }
  }

  // Append Error Message
  function appendErrorMessage(errorText) {
    const row = document.createElement('div');
    row.className = 'message-row assistant-row';
    row.innerHTML = `
      <div class="message-avatar" style="border-color:var(--accent-rose);">⚠️</div>
      <div class="message-content">
        <div class="message-header">
          <span class="sender-name">System Alert</span>
        </div>
        <div class="message-body" style="border-color:var(--accent-rose);background:rgba(244,63,94,0.08);color:#fca5a5;">
          ${escapeHtml(errorText)}
        </div>
      </div>
    `;
    chatMessagesContainer.appendChild(row);
  }

  // Build the Execution Trace Visual Timeline
  function buildTraceWidget(trace, toolsExecuted) {
    if (!trace || trace.length === 0) return '';

    let stepsHtml = '';
    trace.forEach((step) => {
      let icon = '●';
      let cssClass = step.type;

      if (step.type === 'start') icon = '📥';
      else if (step.type === 'thought') icon = '🧠';
      else if (step.type === 'tool_call') icon = '🔧';
      else if (step.type === 'tool_result') icon = '⚙️';
      else if (step.type === 'direct_response') icon = '💬';
      else if (step.type === 'final_answer') icon = '📝';
      else if (step.type === 'error') icon = '⚠️';

      let extraContent = '';
      if (step.type === 'tool_call') {
        extraContent = `
          <div class="trace-step-meta">
            <span style="color:var(--accent-cyan);">args: ${escapeHtml(JSON.stringify(step.arguments))}</span>
            <button class="btn-inspect-tool" data-step-index="${step.step}">🔍 Inspect</button>
          </div>
        `;
      } else if (step.type === 'tool_result') {
        const duration = step.duration_ms ? ` (${step.duration_ms}ms)` : '';
        extraContent = `
          <div class="trace-step-meta">
            <span style="color:var(--accent-green);">${step.message || 'Result generated'}${duration}</span>
            <button class="btn-inspect-tool" data-step-index="${step.step}">🔍 View JSON</button>
          </div>
        `;
      }

      stepsHtml += `
        <div class="trace-step ${cssClass}">
          <div class="trace-step-icon">${icon}</div>
          <div class="trace-step-body">
            <div class="trace-step-label">${escapeHtml(step.message || step.type)}</div>
            ${extraContent}
          </div>
        </div>
      `;
    });

    return `
      <div class="trace-card open">
        <div class="trace-header">
          <div class="trace-title">
            <span>⚡ Agent Execution Trace</span>
            <span class="trace-count-pill">${toolsExecuted} tool call(s)</span>
          </div>
          <span class="trace-chevron">▼</span>
        </div>
        <div class="trace-timeline">
          ${stepsHtml}
        </div>
      </div>
    `;
  }

  // Open Tool Inspector Modal
  function openInspector(traceItem) {
    currentInspectorData = traceItem;
    inspectorTitle.textContent = `🔧 Inspector: ${traceItem.tool || traceItem.type}`;

    if (traceItem.type === 'tool_call') {
      inspectorInput.textContent = JSON.stringify(traceItem.arguments || {}, null, 2);
      inspectorOutput.textContent = 'Awaiting execution...';
    } else if (traceItem.type === 'tool_result') {
      inspectorInput.textContent = JSON.stringify({ tool: traceItem.tool }, null, 2);
      inspectorOutput.textContent = JSON.stringify(traceItem.result || {}, null, 2);
    } else {
      inspectorInput.textContent = JSON.stringify(traceItem, null, 2);
      inspectorOutput.textContent = 'N/A';
    }

    inspectorModal.style.display = 'flex';
  }

  function openSchemaModal(toolName) {
    const tool = state.toolsRegistry[toolName];
    if (!tool) return;
    inspectorTitle.textContent = `📋 Tool Schema: ${tool.name}`;
    inspectorInput.textContent = JSON.stringify(tool.parameters, null, 2);
    inspectorOutput.textContent = JSON.stringify({
      name: tool.name,
      description: tool.description,
    }, null, 2);
    currentInspectorData = tool;
    inspectorModal.style.display = 'flex';
  }

  // Helper Utilities
  function scrollToBottom() {
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  }

  function escapeHtml(str) {
    if (typeof str !== 'string') return String(str);
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Event Listeners Setup
  function setupEventListeners() {
    // Form submit
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleSendMessage();
    });

    // Keyboard enter submit
    userInputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });

    // Auto-grow textarea
    userInputField.addEventListener('input', () => {
      userInputField.style.height = 'auto';
      userInputField.style.height = `${Math.min(userInputField.scrollHeight, 150)}px`;
    });

    // Clear chat
    btnClearChat.addEventListener('click', () => {
      state.conversationHistory = [];
      const messages = chatMessagesContainer.querySelectorAll('.message-row:not(.welcome-banner)');
      messages.forEach((m) => m.remove());
    });

    // Tool toggle checkboxes
    document.querySelectorAll('.tool-checkbox').forEach((cb) => {
      cb.addEventListener('change', updateEnabledTools);
    });

    // View Schema buttons
    document.querySelectorAll('[data-view-schema]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const toolName = btn.getAttribute('data-view-schema');
        openSchemaModal(toolName);
      });
    });

    // Demo buttons
    document.querySelectorAll('.demo-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const action = btn.getAttribute('data-action');
        const query = btn.getAttribute('data-query');

        if (action === 'disable-weather') {
          // Uncheck weather tool checkbox
          const weatherCb = document.getElementById('tool-cb-weather');
          if (weatherCb) {
            weatherCb.checked = false;
            updateEnabledTools();
          }
        }

        userInputField.value = query;
        handleSendMessage(query);
      });
    });

    // Settings Modal
    btnSettingsToggle.addEventListener('click', () => {
      settingsModal.style.display = 'flex';
    });

    btnCloseSettings.addEventListener('click', () => {
      settingsModal.style.display = 'none';
    });

    settingTemperature.addEventListener('input', () => {
      valTemperature.textContent = settingTemperature.value;
    });

    settingMaxTools.addEventListener('input', () => {
      valMaxTools.textContent = settingMaxTools.value;
    });

    btnSaveSettings.addEventListener('click', () => {
      state.settings.model = settingModel.value.trim() || state.settings.model;
      state.settings.temperature = parseFloat(settingTemperature.value);
      state.settings.maxToolCalls = parseInt(settingMaxTools.value, 10);
      modelNameText.textContent = state.settings.model;
      settingsModal.style.display = 'none';
    });

    // Inspector Modal Close & Copy
    btnCloseInspector.addEventListener('click', () => {
      inspectorModal.style.display = 'none';
    });
    btnCloseInspectorAction.addEventListener('click', () => {
      inspectorModal.style.display = 'none';
    });

    btnCopyInspector.addEventListener('click', () => {
      if (currentInspectorData) {
        navigator.clipboard.writeText(JSON.stringify(currentInspectorData, null, 2));
        btnCopyInspector.textContent = '✅ Copied!';
        setTimeout(() => {
          btnCopyInspector.textContent = '📋 Copy JSON';
        }, 1500);
      }
    });

    // Close modals on clicking backdrop
    window.addEventListener('click', (e) => {
      if (e.target === settingsModal) settingsModal.style.display = 'none';
      if (e.target === inspectorModal) inspectorModal.style.display = 'none';
    });
  }

  init();
});
