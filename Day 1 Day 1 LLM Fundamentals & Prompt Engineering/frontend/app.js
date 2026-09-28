/**
 * PromptLab AI - Frontend Application Controller
 * Handles user interactions, strategy transitions, live prompt inspection,
 * API requests, structured JSON formatting, markdown rendering, and comparison.
 */

// ==============================================================================
// State Management
// ==============================================================================
const state = {
  strategy: "zero_shot",
  model: "gpt-4o-mini",
  temperature: 0.3,
  lastResponseData: null,
  history: JSON.parse(localStorage.getItem("promptlab_history") || "[]")
};

// Prebuilt Prompt Engineering Examples
const PREBUILT_EXAMPLES = {
  "ex-summary": {
    prompt: "Summarize the key architectural differences between monolithic and microservice architectures for a junior developer in 5 bullet points.",
    strategy: "zero_shot",
    role: "Senior Enterprise Software Architect",
    objective: "Deliver a clean, 5-point comparative summary of monoliths vs microservices.",
    context: "Junior developer seeking architectural clarity before a technical design review.",
    constraints: "Strictly 5 bullet points. Define trade-offs clearly without jargon.",
    format: "Markdown bullet list with bold takeaways."
  },
  "ex-classify": {
    prompt: "Customer review: 'The new dashboard loads in under a second and the UI is beautiful, but the PDF export button threw a 500 server error when our CFO tried downloading our monthly audit.' Classify sentiment and primary category.",
    strategy: "few_shot",
    role: "Lead QA & Support Triage Specialist",
    objective: "Classify incoming customer feedback following the demonstration format.",
    context: "Automated support triage pipeline prioritizing critical workflow bugs.",
    constraints: "Output format must strictly match: Category, Sentiment, Severity, Action Item.",
    format: "Category: ...\nSentiment: ...\nSeverity: ...\nAction Item: ..."
  },
  "ex-tech": {
    prompt: "Explain the mechanics of backpropagation in deep neural networks to a computer science undergraduate.",
    strategy: "role",
    role: "Distinguished Professor of Artificial Intelligence & Deep Learning",
    objective: "Explain backpropagation clearly connecting the chain rule of calculus to gradient updates.",
    context: "Undergraduate student who understands matrix multiplication and derivatives.",
    constraints: "Provide mathematical intuition first, then algorithmic steps. Max 300 words.",
    format: "1. Core Intuition\n2. The Chain Rule Connection\n3. Weight Update Step"
  },
  "ex-ds": {
    prompt: "Explain the fundamental differences between classification and regression in supervised machine learning, including loss functions and evaluation metrics.",
    strategy: "expert",
    role: "Principal Machine Learning Engineer & Technical Author",
    objective: "Provide a rigorous comparison of classification vs regression models.",
    context: "Data science bootcamp graduates preparing for industry machine learning interviews.",
    constraints: "- Clear section headings\n- Include at least 2 distinct loss functions and evaluation metrics for each\n- Highlight common edge cases\n- Maximum 350 words",
    format: "Structured Markdown with Executive Summary, Loss Functions, Metrics, and Trade-offs."
  },
  "ex-structured": {
    prompt: "Create a focused 7-day Python learning plan for an aspiring AI developer who already knows basic programming concepts.",
    strategy: "structured",
    role: "Curriculum Architect for Applied AI Agents",
    objective: "Structure a comprehensive 7-day learning plan into validated JSON.",
    context: "Developer with general programming literacy transitioning to Python for AI/ML.",
    constraints: "Return 100% valid JSON matching the requested schema. No conversational wrapper.",
    format: `{
  "summary": "Overview of the 7-day syllabus",
  "key_points": ["Day 1-2 Focus", "Day 3-4 Focus", "Day 5-7 Focus"],
  "examples": ["Hands-on project 1", "Hands-on project 2"],
  "next_steps": ["Recommended day 8 action"]
}`
  }
};

// ==============================================================================
// DOM Element References
// ==============================================================================
const elements = {
  // Header
  apiStatusBadge: document.getElementById("api-status-badge"),
  apiStatusText: document.getElementById("api-status-text"),
  headerModelSelect: document.getElementById("header-model-select"),
  btnResetAll: document.getElementById("btn-reset-all"),

  // Strategy & Builder
  strategyCards: document.querySelectorAll(".strategy-card"),
  toggleBuilderFields: document.getElementById("toggle-builder-fields"),
  builderFieldsBody: document.getElementById("builder-fields-body"),
  builderRole: document.getElementById("builder-role"),
  builderObjective: document.getElementById("builder-objective"),
  builderContext: document.getElementById("builder-context"),
  builderConstraints: document.getElementById("builder-constraints"),
  builderOutputFormat: document.getElementById("builder-output-format"),

  // Checklist Chips
  chkRole: document.getElementById("chk-role"),
  chkObjective: document.getElementById("chk-objective"),
  chkContext: document.getElementById("chk-context"),
  chkConstraints: document.getElementById("chk-constraints"),
  chkFormat: document.getElementById("chk-format"),
  chkInput: document.getElementById("chk-input"),

  // Model Settings
  tempSlider: document.getElementById("temperature-slider"),
  tempValue: document.getElementById("temp-value"),
  tempLabel: document.getElementById("temp-label"),

  // Main Input
  userPromptInput: document.getElementById("user-prompt-input"),
  charCounter: document.getElementById("char-counter"),
  btnClearInput: document.getElementById("btn-clear-input"),
  currentStrategyBadge: document.getElementById("current-strategy-badge"),
  btnGenerate: document.getElementById("btn-generate"),
  btnGenerateText: document.getElementById("btn-generate-text"),
  btnSpinner: document.getElementById("btn-spinner"),
  btnOpenCompare: document.getElementById("btn-open-compare"),

  // Examples
  examplesPills: document.querySelectorAll(".pill-btn"),

  // Results & Tabs
  tabs: document.querySelectorAll(".tab-btn"),
  tabPanes: document.querySelectorAll(".tab-pane"),

  // Response Pane
  chipStatus: document.getElementById("chip-status"),
  chipModel: document.getElementById("chip-model"),
  chipLatency: document.getElementById("chip-latency"),
  chipTokens: document.getElementById("chip-tokens"),
  chipStructured: document.getElementById("chip-structured"),
  btnCopyResponse: document.getElementById("btn-copy-response"),
  copyBtnText: document.getElementById("copy-btn-text"),
  btnDownloadTxt: document.getElementById("btn-download-txt"),
  validationAlert: document.getElementById("validation-alert"),
  validationAlertMsg: document.getElementById("validation-alert-msg"),
  errorBanner: document.getElementById("error-banner"),
  errorTitle: document.getElementById("error-title"),
  errorMessage: document.getElementById("error-message"),
  responseBody: document.getElementById("response-body"),

  // Prompt Inspector Pane
  btnCopyPrompt: document.getElementById("btn-copy-prompt"),
  inspectorSystemPrompt: document.getElementById("inspector-system-prompt"),
  inspectorUserPrompt: document.getElementById("inspector-user-prompt"),
  inspectorStrategyBadge: document.getElementById("inspector-strategy-badge"),
  metaStrategy: document.getElementById("meta-strategy"),
  metaOutputFmt: document.getElementById("meta-output-fmt"),
  metaModel: document.getElementById("meta-model"),
  metaTemp: document.getElementById("meta-temp"),

  // History Pane
  historyCount: document.getElementById("history-count"),
  historySearch: document.getElementById("history-search"),
  historyList: document.getElementById("history-list"),
  btnClearHistory: document.getElementById("btn-clear-history"),

  // Compare Modal
  compareModal: document.getElementById("compare-modal"),
  btnCloseCompare: document.getElementById("btn-close-compare"),
  compareStrategyA: document.getElementById("compare-strategy-a"),
  compareStrategyB: document.getElementById("compare-strategy-b"),
  btnRunCompare: document.getElementById("btn-run-compare"),
  titleCompareA: document.getElementById("title-compare-a"),
  titleCompareB: document.getElementById("title-compare-b"),
  metaCompareA: document.getElementById("meta-compare-a"),
  metaCompareB: document.getElementById("meta-compare-b"),
  bodyCompareA: document.getElementById("body-compare-a"),
  bodyCompareB: document.getElementById("body-compare-b"),

  // Toasts
  toastContainer: document.getElementById("toast-container")
};

// ==============================================================================
// Utility Functions
// ==============================================================================

function showToast(message, duration = 3000) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Lightweight safe markdown renderer for clean display of headings, bold, code, and lists.
 */
function renderMarkdown(md) {
  if (!md) return "";
  let html = escapeHtml(md);

  // Fenced Code blocks
  html = html.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code class="language-${lang}">${code}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");

  // Headings
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Blockquotes
  html = html.replace(/^\> (.*$)/gim, "<blockquote>$1</blockquote>");

  // Bullet items
  html = html.replace(/^\s*[\-\*]\s+(.*$)/gim, "<li>$1</li>");
  html = html.replace(/(<li>[\s\S]*?<\/li>)/gi, "<ul>$1</ul>");
  // Clean up nested repeated <ul> tags
  html = html.replace(/<\/ul>\s*<ul>/gi, "");

  // Ordered list items
  html = html.replace(/^\s*\d+\.\s+(.*$)/gim, "<li>$1</li>");

  // Paragraphs
  html = html.split(/\n{2,}/).map(para => {
    para = para.trim();
    if (para.startsWith("<h") || para.startsWith("<ul") || para.startsWith("<ol") || para.startsWith("<pre")) {
      return para;
    }
    return `<p>${para.replace(/\n/g, "<br>")}</p>`;
  }).join("\n");

  return html;
}

/**
 * Pretty formats a JSON object with syntax highlighting classes.
 */
function formatJsonDisplay(obj) {
  const jsonStr = JSON.stringify(obj, null, 2);
  return `<pre class="json-display">${escapeHtml(jsonStr)}</pre>`;
}

// ==============================================================================
// Quality Checklist & Live Validation
// ==============================================================================
function updateQualityChecklist() {
  const roleVal = elements.builderRole.value.trim();
  const objVal = elements.builderObjective.value.trim();
  const ctxVal = elements.builderContext.value.trim();
  const consVal = elements.builderConstraints.value.trim();
  const fmtVal = elements.builderOutputFormat.value.trim();
  const inputVal = elements.userPromptInput.value.trim();

  elements.chkRole.classList.toggle("active", roleVal.length > 0);
  elements.chkObjective.classList.toggle("active", objVal.length > 0);
  elements.chkContext.classList.toggle("active", ctxVal.length > 0);
  elements.chkConstraints.classList.toggle("active", consVal.length > 0);
  elements.chkFormat.classList.toggle("active", fmtVal.length > 0);
  elements.chkInput.classList.toggle("active", inputVal.length > 0);

  // Character counter
  const charLen = inputVal.length;
  elements.charCounter.textContent = `${charLen.toLocaleString()} / 10,000`;
  elements.charCounter.style.color = charLen > 9000 ? "var(--status-error)" : "var(--text-dim)";
}

// ==============================================================================
// Strategy Switching
// ==============================================================================
function setStrategy(strategyKey) {
  state.strategy = strategyKey;

  // Update card active classes
  elements.strategyCards.forEach(card => {
    card.classList.toggle("active", card.getAttribute("data-strategy") === strategyKey);
  });

  const names = {
    zero_shot: "Zero-Shot",
    few_shot: "Few-Shot",
    role: "Role Prompting",
    structured: "Structured JSON",
    expert: "Expert + Constraints"
  };

  elements.currentStrategyBadge.textContent = names[strategyKey] || strategyKey;
  elements.metaStrategy.textContent = names[strategyKey] || strategyKey;
  elements.inspectorStrategyBadge.textContent = strategyKey;

  // Provide helpful defaults if fields are empty
  if (strategyKey === "structured" && !elements.builderOutputFormat.value.trim()) {
    elements.builderOutputFormat.value = "JSON object with summary, key_points, examples, next_steps";
  } else if (strategyKey === "role" && !elements.builderRole.value.trim()) {
    elements.builderRole.value = "Senior Machine Learning Engineer";
  } else if (strategyKey === "expert") {
    if (!elements.builderRole.value.trim()) elements.builderRole.value = "Principal AI Solutions Architect";
    if (!elements.builderObjective.value.trim()) elements.builderObjective.value = "Provide an in-depth, structured technical analysis.";
    if (!elements.builderConstraints.value.trim()) elements.builderConstraints.value = "- Focus on production trade-offs\n- Highlight failure modes\n- Maximum 350 words";
  }

  updateQualityChecklist();
}

// ==============================================================================
// Prebuilt Example Loader
// ==============================================================================
function loadExample(exampleKey) {
  const ex = PREBUILT_EXAMPLES[exampleKey];
  if (!ex) return;

  elements.userPromptInput.value = ex.prompt;
  setStrategy(ex.strategy);

  elements.builderRole.value = ex.role || "";
  elements.builderObjective.value = ex.objective || "";
  elements.builderContext.value = ex.context || "";
  elements.builderConstraints.value = ex.constraints || "";
  elements.builderOutputFormat.value = ex.format || "";

  updateQualityChecklist();
  showToast(`Loaded "${exampleKey.replace('ex-', '').toUpperCase()}" example prompt.`);
}

// ==============================================================================
// Tabs Controller
// ==============================================================================
function activateTab(tabId) {
  elements.tabs.forEach(btn => btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId));
  elements.tabPanes.forEach(pane => pane.classList.toggle("active", pane.id === tabId));
}

// ==============================================================================
// Temperature Slider Handling
// ==============================================================================
function updateTemperature(val) {
  state.temperature = parseFloat(val);
  elements.tempValue.textContent = state.temperature.toFixed(2);
  elements.metaTemp.textContent = state.temperature.toFixed(2);

  if (state.temperature <= 0.2) {
    elements.tempLabel.textContent = "Deterministic & Strict";
    elements.tempLabel.style.color = "#34d399";
  } else if (state.temperature <= 0.6) {
    elements.tempLabel.textContent = "Balanced & Analytical";
    elements.tempLabel.style.color = "#38bdf8";
  } else {
    elements.tempLabel.textContent = "Creative & Exploratory";
    elements.tempLabel.style.color = "#f59e0b";
  }
}

// ==============================================================================
// History Management (Local Storage)
// ==============================================================================
function savePromptToHistory(userPrompt, strategy, model, responseSnippet) {
  const item = {
    id: Date.now(),
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    date: new Date().toLocaleDateString(),
    userPrompt,
    strategy,
    model,
    responseSnippet: responseSnippet.slice(0, 120) + (responseSnippet.length > 120 ? "..." : "")
  };

  state.history.unshift(item);
  if (state.history.length > 30) state.history.pop();
  localStorage.setItem("promptlab_history", JSON.stringify(state.history));
  renderHistory();
}

function renderHistory() {
  elements.historyCount.textContent = state.history.length;
  const filter = (elements.historySearch.value || "").toLowerCase();

  const filtered = state.history.filter(item =>
    item.userPrompt.toLowerCase().includes(filter) ||
    item.strategy.toLowerCase().includes(filter)
  );

  if (filtered.length === 0) {
    elements.historyList.innerHTML = `
      <div class="empty-state">
        <p>${state.history.length === 0 ? "No saved prompts yet." : "No matching prompts found in search."}</p>
      </div>`;
    return;
  }

  elements.historyList.innerHTML = filtered.map(item => `
    <div class="history-item">
      <div class="history-item-left" data-id="${item.id}">
        <div class="history-item-top">
          <span class="history-strat-tag">${escapeHtml(item.strategy)}</span>
          <span class="history-time">${escapeHtml(item.date)} ${escapeHtml(item.timestamp)}</span>
        </div>
        <div class="history-snippet">${escapeHtml(item.userPrompt)}</div>
      </div>
      <button class="btn-icon btn-del-history" data-id="${item.id}" title="Delete entry">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
        </svg>
      </button>
    </div>
  `).join("");

  // Attach reload listeners
  document.querySelectorAll(".history-item-left").forEach(el => {
    el.addEventListener("click", () => {
      const id = parseInt(el.getAttribute("data-id"));
      const item = state.history.find(h => h.id === id);
      if (item) {
        elements.userPromptInput.value = item.userPrompt;
        setStrategy(item.strategy);
        activateTab("tab-response");
        showToast("Restored prompt from history.");
      }
    });
  });

  // Attach delete listeners
  document.querySelectorAll(".btn-del-history").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = parseInt(btn.getAttribute("data-id"));
      state.history = state.history.filter(h => h.id !== id);
      localStorage.setItem("promptlab_history", JSON.stringify(state.history));
      renderHistory();
      showToast("History entry removed.");
    });
  });
}

// ==============================================================================
// Health / API Connectivity Check
// ==============================================================================
async function checkApiHealth() {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.has_api_key) {
      elements.apiStatusBadge.className = "status-badge status-ready";
      elements.apiStatusText.textContent = `API Ready (${data.masked_key})`;
      elements.apiStatusBadge.title = `LLM Service is configured and ready with model: ${data.default_model}`;
    } else {
      elements.apiStatusBadge.className = "status-badge status-warning";
      elements.apiStatusText.textContent = "API Key Required (.env)";
      elements.apiStatusBadge.title = "OPENAI_API_KEY is not configured in .env. Configure it to enable real generation.";
    }

    if (data.available_models && data.available_models.length > 0) {
      elements.headerModelSelect.innerHTML = data.available_models
        .map(m => `<option value="${m}" ${m === data.default_model ? 'selected' : ''}>${m}</option>`)
        .join("");
    }
  } catch (err) {
    elements.apiStatusBadge.className = "status-badge status-warning";
    elements.apiStatusText.textContent = "API Offline";
    elements.apiStatusBadge.title = "Unable to connect to PromptLab AI backend.";
  }
}

// ==============================================================================
// Core Generation Request
// ==============================================================================
async function handleGenerate() {
  const userInput = elements.userPromptInput.value.trim();

  // Validate input
  if (!userInput) {
    showToast("Please enter a prompt or select a quick example.");
    elements.userPromptInput.focus();
    return;
  }

  if (userInput.length > 10000) {
    showToast("Input exceeds maximum character length of 10,000.");
    return;
  }

  // Set loading state
  elements.btnGenerate.disabled = true;
  elements.btnGenerateText.textContent = "Generating...";
  elements.btnSpinner.classList.remove("hidden");

  elements.chipStatus.className = "chip-metric chip-idle";
  elements.chipStatus.textContent = "Status: Calling API...";
  elements.errorBanner.classList.add("hidden");
  elements.validationAlert.classList.add("hidden");
  elements.chipStructured.classList.add("hidden");

  // Construct payload
  const payload = {
    user_input: userInput,
    strategy: state.strategy,
    role: elements.builderRole.value.trim() || null,
    objective: elements.builderObjective.value.trim() || null,
    context: elements.builderContext.value.trim() || null,
    constraints: elements.builderConstraints.value.trim() || null,
    output_format: elements.builderOutputFormat.value.trim() || null,
    model: state.model,
    temperature: state.temperature
  };

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    state.lastResponseData = data;

    if (res.ok && data.success) {
      // Success State
      elements.chipStatus.className = "chip-metric chip-success";
      elements.chipStatus.textContent = "Status: Success (200 OK)";
      elements.chipModel.textContent = `Model: ${data.model}`;
      elements.chipLatency.textContent = `Latency: ${data.latency_ms || "--"} ms`;

      if (data.usage) {
        elements.chipTokens.textContent = `Tokens: ${data.usage.total_tokens} (P: ${data.usage.prompt_tokens} / C: ${data.usage.completion_tokens})`;
      } else {
        elements.chipTokens.textContent = "Tokens: N/A";
      }

      // Render response content
      if (data.structured && data.parsed_json) {
        elements.chipStructured.classList.remove("hidden");
        elements.chipStructured.textContent = "Structured JSON Validated";
        elements.responseBody.innerHTML = formatJsonDisplay(data.parsed_json);
      } else {
        elements.responseBody.innerHTML = renderMarkdown(data.response);
      }

      // Display soft validation warnings if any
      if (data.validation_error) {
        elements.validationAlert.classList.remove("hidden");
        elements.validationAlertMsg.textContent = data.validation_error;
      }

      // Populate Prompt Inspector
      if (data.prompt_inspector) {
        elements.inspectorSystemPrompt.textContent = data.prompt_inspector.system_prompt;
        elements.inspectorUserPrompt.textContent = data.prompt_inspector.generated_prompt;
        elements.metaOutputFmt.textContent = data.prompt_inspector.output_format;
        elements.metaModel.textContent = data.prompt_inspector.model_settings.model;
        elements.metaTemp.textContent = data.prompt_inspector.model_settings.temperature;
      }

      // Save to history
      savePromptToHistory(userInput, data.strategy, data.model, data.response);
      showToast("Response generated successfully!");

    } else {
      // Failure / Error state
      elements.chipStatus.className = "chip-metric chip-error";
      elements.chipStatus.textContent = "Status: Error";
      elements.chipLatency.textContent = `Latency: ${data.latency_ms || "--"} ms`;

      elements.errorBanner.classList.remove("hidden");
      elements.errorTitle.textContent = data.error || "Generation Failed";
      elements.errorMessage.textContent = data.response || "Unable to contact the LLM service. Please check your API configuration and try again.";

      elements.responseBody.innerHTML = `
        <div class="empty-state">
          <p style="color: var(--status-error);">${escapeHtml(data.response || "Request failed.")}</p>
        </div>`;

      if (data.prompt_inspector) {
        elements.inspectorSystemPrompt.textContent = data.prompt_inspector.system_prompt;
        elements.inspectorUserPrompt.textContent = data.prompt_inspector.generated_prompt;
      }

      showToast("Generation error. Check details.", 4000);
    }
  } catch (err) {
    elements.chipStatus.className = "chip-metric chip-error";
    elements.chipStatus.textContent = "Status: Network Error";
    elements.errorBanner.classList.remove("hidden");
    elements.errorTitle.textContent = "Connection Failure";
    elements.errorMessage.textContent = "Unable to contact PromptLab AI backend. Ensure the server is running on http://127.0.0.1:8000.";
    showToast("Network failure contacting backend.", 4000);
  } finally {
    elements.btnGenerate.disabled = false;
    elements.btnGenerateText.textContent = "Generate Response";
    elements.btnSpinner.classList.add("hidden");
    activateTab("tab-response");
  }
}

// ==============================================================================
// Strategy Comparison Feature
// ==============================================================================
async function handleRunComparison() {
  const userInput = elements.userPromptInput.value.trim();
  if (!userInput) {
    showToast("Please enter a user request in the input box first.");
    elements.compareModal.classList.add("hidden");
    elements.userPromptInput.focus();
    return;
  }

  const stratA = elements.compareStrategyA.value;
  const stratB = elements.compareStrategyB.value;

  if (stratA === stratB) {
    showToast("Please select two different strategies to compare.");
    return;
  }

  elements.btnRunCompare.disabled = true;
  elements.btnRunCompare.querySelector("span").textContent = "Comparing...";

  elements.bodyCompareA.innerHTML = '<div class="empty-state">Executing Strategy A...</div>';
  elements.bodyCompareB.innerHTML = '<div class="empty-state">Executing Strategy B...</div>';

  const payload = {
    user_input: userInput,
    strategy_a: stratA,
    strategy_b: stratB,
    role: elements.builderRole.value.trim() || null,
    objective: elements.builderObjective.value.trim() || null,
    context: elements.builderContext.value.trim() || null,
    constraints: elements.builderConstraints.value.trim() || null,
    output_format: elements.builderOutputFormat.value.trim() || null,
    model: state.model,
    temperature: state.temperature
  };

  try {
    const res = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok && data.result_a && data.result_b) {
      const a = data.result_a;
      const b = data.result_b;

      // Populate A
      elements.titleCompareA.textContent = `Strategy A (${a.strategy.toUpperCase()})`;
      elements.metaCompareA.innerHTML = `<span>Latency: ${a.latency_ms || "--"} ms</span> | <span>Length: ${a.response.length} chars</span>`;
      elements.bodyCompareA.innerHTML = a.structured && a.parsed_json ? formatJsonDisplay(a.parsed_json) : renderMarkdown(a.response);

      // Populate B
      elements.titleCompareB.textContent = `Strategy B (${b.strategy.toUpperCase()})`;
      elements.metaCompareB.innerHTML = `<span>Latency: ${b.latency_ms || "--"} ms</span> | <span>Length: ${b.response.length} chars</span>`;
      elements.bodyCompareB.innerHTML = b.structured && b.parsed_json ? formatJsonDisplay(b.parsed_json) : renderMarkdown(b.response);

      showToast("Strategy comparison complete!");
    } else {
      showToast("Comparison returned an error. Check server logs.", 4000);
    }
  } catch (err) {
    showToast("Network error during comparison.", 4000);
  } finally {
    elements.btnRunCompare.disabled = false;
    elements.btnRunCompare.querySelector("span").textContent = "Run Comparison";
  }
}

// ==============================================================================
// Copy & Download Handlers
// ==============================================================================
function copyTextToClipboard(text, successCallback) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(successCallback).catch(() => fallbackCopy(text, successCallback));
  } else {
    fallbackCopy(text, successCallback);
  }
}

function fallbackCopy(text, successCallback) {
  const ta = document.createElement("textarea");
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
  if (successCallback) successCallback();
}

function handleDownloadResponse() {
  if (!state.lastResponseData || !state.lastResponseData.response) {
    showToast("No response available to export.");
    return;
  }

  const isJson = state.lastResponseData.structured && state.lastResponseData.parsed_json;
  const filename = `promptlab-response-${Date.now()}.${isJson ? "json" : "txt"}`;
  const content = isJson
    ? JSON.stringify(state.lastResponseData.parsed_json, null, 2)
    : state.lastResponseData.response;

  const blob = new Blob([content], { type: isJson ? "application/json" : "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(`Exported as ${filename}`);
}

// ==============================================================================
// Event Listeners Setup
// ==============================================================================
function initEventListeners() {
  // Strategy Cards Selection
  elements.strategyCards.forEach(card => {
    card.addEventListener("click", () => {
      const s = card.getAttribute("data-strategy");
      setStrategy(s);
    });
  });

  // Prompt Builder Input Listeners for Quality Checklist
  [
    elements.builderRole,
    elements.builderObjective,
    elements.builderContext,
    elements.builderConstraints,
    elements.builderOutputFormat,
    elements.userPromptInput
  ].forEach(input => {
    input.addEventListener("input", updateQualityChecklist);
  });

  // Toggle Builder Fields
  elements.toggleBuilderFields.addEventListener("click", () => {
    const isCollapsed = elements.builderFieldsBody.classList.toggle("collapsed");
    elements.toggleBuilderFields.textContent = isCollapsed ? "Expand" : "Collapse";
  });

  // Quick Examples Pills
  elements.examplesPills.forEach(pill => {
    pill.addEventListener("click", () => {
      const exKey = pill.getAttribute("data-example");
      loadExample(exKey);
    });
  });

  // Clear Input Button
  elements.btnClearInput.addEventListener("click", () => {
    elements.userPromptInput.value = "";
    updateQualityChecklist();
    elements.userPromptInput.focus();
  });

  // Temperature Slider
  elements.tempSlider.addEventListener("input", (e) => {
    updateTemperature(e.target.value);
  });

  // Header Model Selector
  elements.headerModelSelect.addEventListener("change", (e) => {
    state.model = e.target.value;
    elements.metaModel.textContent = state.model;
    showToast(`Model set to ${state.model}`);
  });

  // Tabs Navigation
  elements.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      activateTab(target);
    });
  });

  // Generate Button
  elements.btnGenerate.addEventListener("click", handleGenerate);

  // Ctrl+Enter or Cmd+Enter to generate
  elements.userPromptInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleGenerate();
    }
  });

  // Copy Response
  elements.btnCopyResponse.addEventListener("click", () => {
    if (!state.lastResponseData || !state.lastResponseData.response) {
      showToast("No response to copy.");
      return;
    }
    const textToCopy = (state.lastResponseData.structured && state.lastResponseData.parsed_json)
      ? JSON.stringify(state.lastResponseData.parsed_json, null, 2)
      : state.lastResponseData.response;

    copyTextToClipboard(textToCopy, () => {
      elements.copyBtnText.textContent = "Copied!";
      setTimeout(() => elements.copyBtnText.textContent = "Copy", 2000);
      showToast("Response copied to clipboard.");
    });
  });

  // Export / Download
  elements.btnDownloadTxt.addEventListener("click", handleDownloadResponse);

  // Copy Prompt Inspector
  elements.btnCopyPrompt.addEventListener("click", () => {
    const text = elements.inspectorUserPrompt.textContent;
    copyTextToClipboard(text, () => {
      showToast("Dispatched prompt copied to clipboard.");
    });
  });

  // History Search & Clear
  elements.historySearch.addEventListener("input", renderHistory);
  elements.btnClearHistory.addEventListener("click", () => {
    state.history = [];
    localStorage.removeItem("promptlab_history");
    renderHistory();
    showToast("History cleared.");
  });

  // Comparison Modal Open / Close
  elements.btnOpenCompare.addEventListener("click", () => {
    elements.compareModal.classList.remove("hidden");
  });
  elements.btnCloseCompare.addEventListener("click", () => {
    elements.compareModal.classList.add("hidden");
  });
  elements.compareModal.addEventListener("click", (e) => {
    if (e.target === elements.compareModal) {
      elements.compareModal.classList.add("hidden");
    }
  });
  elements.btnRunCompare.addEventListener("click", handleRunComparison);

  // Reset All Button
  elements.btnResetAll.addEventListener("click", () => {
    elements.userPromptInput.value = "";
    elements.builderRole.value = "";
    elements.builderObjective.value = "";
    elements.builderContext.value = "";
    elements.builderConstraints.value = "";
    elements.builderOutputFormat.value = "";
    setStrategy("zero_shot");
    updateTemperature(0.3);
    elements.tempSlider.value = 0.3;
    updateQualityChecklist();
    showToast("All fields reset to defaults.");
  });
}

// ==============================================================================
// Initialization
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  updateQualityChecklist();
  renderHistory();
  checkApiHealth();
});
