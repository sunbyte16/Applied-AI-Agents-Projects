/**
 * DocuRAG AI - Client-Side Controller
 * Document Intelligence & Retrieval-Augmented Q&A
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let conversationHistory = [];
  let latestQueryResponse = null;
  let isQuerying = false;

  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const uploadProgressContainer = document.getElementById("uploadProgressContainer");
  const uploadProgressBar = document.getElementById("uploadProgressBar");
  const uploadStatusText = document.getElementById("uploadStatusText");

  const documentList = document.getElementById("documentList");
  const docFilterSelect = document.getElementById("docFilterSelect");
  const refreshDocsBtn = document.getElementById("refreshDocsBtn");

  const topKInput = document.getElementById("topKInput");
  const topKVal = document.getElementById("topKVal");
  const chunkSizeInput = document.getElementById("chunkSizeInput");
  const chunkSizeVal = document.getElementById("chunkSizeVal");
  const chunkOverlapInput = document.getElementById("chunkOverlapInput");
  const chunkOverlapVal = document.getElementById("chunkOverlapVal");
  const tempInput = document.getElementById("tempInput");
  const tempVal = document.getElementById("tempVal");

  const questionInput = document.getElementById("questionInput");
  const askBtn = document.getElementById("askBtn");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const chatMessages = document.getElementById("chatMessages");

  const retrievedChunksList = document.getElementById("retrievedChunksList");
  const inspectorSummary = document.getElementById("inspectorSummary");
  const retrievedCountBadge = document.getElementById("retrievedCountBadge");
  const pipelineTotalTime = document.getElementById("pipelineTotalTime");

  const docModal = document.getElementById("docModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");
  const modalCloseBtn = document.getElementById("modalCloseBtn");

  // Status Badges
  const vectorStoreText = document.getElementById("vectorStoreText");
  const providerText = document.getElementById("providerText");
  const totalDocsCount = document.getElementById("totalDocsCount");
  const totalChunksCount = document.getElementById("totalChunksCount");

  // --- Initial Setup ---
  initEventListeners();
  fetchHealthAndStats();
  fetchDocuments();

  // Handle URL params for automated screenshots/demo
  const urlParams = new URLSearchParams(window.location.search);
  const actionParam = urlParams.get("action");
  const tabParam = urlParams.get("tab");

  if (actionParam === "ask") {
    setTimeout(async () => {
      questionInput.value = "What are the core components of a RAG system?";
      await submitQuestion();
      if (tabParam === "context") {
        document.getElementById("contextTabBtn")?.click();
      } else if (tabParam === "pipeline") {
        document.querySelector('.tab-btn[data-tab="pipelineTab"]')?.click();
      }
    }, 500);
  } else if (actionParam === "modal") {
    setTimeout(async () => {
      const res = await fetch("/api/documents");
      const docs = await res.json();
      if (docs.length > 0) {
        inspectDocumentChunks(docs[0].document_id);
      }
    }, 500);
  } else if (tabParam === "context") {
    setTimeout(() => {
      document.getElementById("contextTabBtn")?.click();
    }, 300);
  } else if (tabParam === "pipeline") {
    setTimeout(() => {
      document.querySelector('.tab-btn[data-tab="pipelineTab"]')?.click();
    }, 300);
  }

  function initEventListeners() {
    // Tab switching
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
        btn.classList.add("active");
        const tabId = btn.getAttribute("data-tab");
        const tabContent = document.getElementById(tabId);
        if (tabContent) tabContent.classList.add("active");
      });
    });

    // Settings Sliders
    topKInput.addEventListener("input", (e) => {
      topKVal.textContent = `${e.target.value} chunks`;
    });
    chunkSizeInput.addEventListener("input", (e) => {
      chunkSizeVal.textContent = e.target.value;
    });
    chunkOverlapInput.addEventListener("input", (e) => {
      chunkOverlapVal.textContent = e.target.value;
    });
    tempInput.addEventListener("input", (e) => {
      tempVal.textContent = e.target.value;
    });

    // Upload interactions
    dropZone.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", handleFileSelect);

    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        uploadFile(e.dataTransfer.files[0]);
      }
    });

    // Document Refresh
    refreshDocsBtn.addEventListener("click", () => {
      fetchDocuments();
      fetchHealthAndStats();
    });

    // Chat actions
    askBtn.addEventListener("click", submitQuestion);
    questionInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitQuestion();
      }
    });
    clearChatBtn.addEventListener("click", clearChat);

    // Preset evaluation buttons
    document.querySelectorAll(".btn-preset").forEach((btn) => {
      btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-q");
        questionInput.value = q;
        submitQuestion();
      });
    });

    // Modal close
    modalCloseBtn.addEventListener("click", () => {
      docModal.style.display = "none";
    });
    window.addEventListener("click", (e) => {
      if (e.target === docModal) {
        docModal.style.display = "none";
      }
    });
  }

  // --- API Functions ---

  async function fetchHealthAndStats() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) return;
      const data = await res.json();
      vectorStoreText.textContent = data.vector_store;
      providerText.textContent = `${data.llm_provider} / ${data.embedding_provider.split(" ")[0]}`;
      totalDocsCount.textContent = data.total_documents;
      totalChunksCount.textContent = data.total_chunks;
    } catch (err) {
      console.error("Health check error:", err);
    }
  }

  async function fetchDocuments() {
    try {
      const res = await fetch("/api/documents");
      if (!res.ok) return;
      const docs = await res.json();
      renderDocumentList(docs);
      updateDocFilterSelect(docs);
    } catch (err) {
      console.error("Fetch documents error:", err);
    }
  }

  function renderDocumentList(docs) {
    if (!docs || docs.length === 0) {
      documentList.innerHTML = `<div class="empty-state-small">No documents indexed yet. Upload a document above.</div>`;
      return;
    }

    documentList.innerHTML = docs
      .map(
        (doc) => `
      <div class="doc-item" data-id="${doc.document_id}">
        <div class="doc-info">
          <div class="doc-name-row">
            <span class="type-tag ${doc.file_type}">${doc.file_type}</span>
            <span class="doc-name" title="${doc.document_name}">${doc.document_name}</span>
          </div>
          <span class="doc-meta">${doc.total_chunks} chunks &bull; ${(doc.size_bytes / 1024).toFixed(1)} KB</span>
        </div>
        <div class="doc-actions">
          <button class="btn-icon inspect-doc-btn" data-id="${doc.document_id}" title="Inspect Chunks">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
          </button>
          <button class="btn-icon danger delete-doc-btn" data-id="${doc.document_id}" title="Delete Document">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
    `
      )
      .join("");

    // Attach click events
    document.querySelectorAll(".inspect-doc-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        inspectDocumentChunks(btn.getAttribute("data-id"));
      });
    });

    document.querySelectorAll(".delete-doc-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        deleteDocument(btn.getAttribute("data-id"));
      });
    });
  }

  function updateDocFilterSelect(docs) {
    const currentVal = docFilterSelect.value;
    docFilterSelect.innerHTML = `<option value="all">Search all documents (Multi-doc)</option>`;
    docs.forEach((d) => {
      const opt = document.createElement("option");
      opt.value = d.document_id;
      opt.textContent = `${d.document_name} (${d.total_chunks} chunks)`;
      docFilterSelect.appendChild(opt);
    });
    if (docs.some((d) => d.document_id === currentVal)) {
      docFilterSelect.value = currentVal;
    }
  }

  function handleFileSelect(e) {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  }

  async function uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("chunk_size", chunkSizeInput.value);
    formData.append("chunk_overlap", chunkOverlapInput.value);

    uploadProgressContainer.style.display = "block";
    uploadProgressBar.style.width = "40%";
    uploadStatusText.textContent = `Extracting & chunking '${file.name}'...`;

    try {
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      uploadProgressBar.style.width = "85%";
      uploadStatusText.textContent = "Storing vectors in ChromaDB...";

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      uploadProgressBar.style.width = "100%";
      uploadStatusText.textContent = `Success! ${data.chunks_count} chunks indexed in ${data.duration_ms} ms.`;

      // Update pipeline inspector for ingestion
      updatePipelineStage(1, "success", `Extracted text from ${file.name}`);
      updatePipelineStage(2, "success", `Divided into ${data.chunks_count} chunks (size ${chunkSizeInput.value})`);
      updatePipelineStage(3, "success", `Embeddings generated (${data.document.char_count} chars)`);
      updatePipelineStage(4, "success", `Vectors persisted in ChromaDB collection`);

      setTimeout(() => {
        uploadProgressContainer.style.display = "none";
        uploadProgressBar.style.width = "0%";
      }, 3000);

      fetchDocuments();
      fetchHealthAndStats();
      fileInput.value = "";
    } catch (err) {
      uploadProgressBar.style.width = "100%";
      uploadProgressBar.style.background = "var(--danger)";
      uploadStatusText.textContent = `Error: ${err.message}`;
      console.error("Upload error:", err);
      setTimeout(() => {
        uploadProgressContainer.style.display = "none";
        uploadProgressBar.style.width = "0%";
        uploadProgressBar.style.background = "linear-gradient(90deg, var(--accent-primary), var(--accent-cyan))";
      }, 4000);
    }
  }

  async function deleteDocument(docId) {
    if (!confirm("Are you sure you want to delete this document and remove its vectors from ChromaDB?")) {
      return;
    }
    try {
      const res = await fetch(`/api/documents/${docId}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete");
      fetchDocuments();
      fetchHealthAndStats();
    } catch (err) {
      alert(`Deletion error: ${err.message}`);
    }
  }

  async function inspectDocumentChunks(docId) {
    modalTitle.textContent = "Loading Document Chunks...";
    modalBody.innerHTML = `<div class="empty-state-small">Fetching chunks from ChromaDB...</div>`;
    docModal.style.display = "flex";

    try {
      const res = await fetch(`/api/documents/${docId}/chunks`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to load chunks");

      modalTitle.textContent = `${data.document_name} — All ${data.total_chunks} Chunks`;
      modalBody.innerHTML = data.chunks
        .map(
          (c) => `
        <div style="background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 6px;">
            <span style="color: var(--accent-cyan); font-weight: 600;">Chunk #${c.metadata.chunk_id}</span>
            <span style="color: var(--text-dim);">${c.metadata.page !== -1 ? `Page ${c.metadata.page}` : "Page N/A"} &bull; ${c.metadata.char_count} chars</span>
          </div>
          <pre style="font-family: var(--font-mono); font-size: 11px; color: #cbd5e1; white-space: pre-wrap; word-break: break-word;">${escapeHtml(c.text)}</pre>
        </div>
      `
        )
        .join("");
    } catch (err) {
      modalBody.innerHTML = `<div style="color: var(--danger);">Error: ${err.message}</div>`;
    }
  }

  // --- RAG Query Pipeline ---

  async function submitQuestion() {
    const question = questionInput.value.trim();
    if (!question || isQuerying) return;

    isQuerying = true;
    askBtn.disabled = true;

    // Remove welcome hero if present
    const welcomeCard = document.querySelector(".welcome-card");
    if (welcomeCard) welcomeCard.remove();

    // Append User Message
    appendMessage("user", question);
    questionInput.value = "";

    // Append Loading Assistant Message
    const loadingId = appendLoadingMessage();

    // Prepare Request
    const selectedDocId = docFilterSelect.value;
    const topK = parseInt(topKInput.value, 10);
    const temperature = parseFloat(tempInput.value);

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: question,
          document_id: selectedDocId,
          top_k: topK,
          temperature: temperature,
          conversation_history: conversationHistory,
        }),
      });

      const data = await res.json();
      removeMessage(loadingId);

      if (!res.ok) {
        throw new Error(data.detail || "Query failed");
      }

      latestQueryResponse = data;

      // Append Assistant Response
      appendAssistantMessage(data.answer, data.sources);

      // Track Conversation History
      conversationHistory.push({ role: "user", content: question });
      conversationHistory.push({ role: "assistant", content: data.answer });

      // Update Inspector Tabs
      updateContextInspector(question, data.sources);
      if (data.pipeline_trace) {
        updatePipelineInspector(data.pipeline_trace);
      }
    } catch (err) {
      removeMessage(loadingId);
      appendAssistantMessage(`An error occurred: ${err.message}`, []);
      console.error("Query error:", err);
    } finally {
      isQuerying = false;
      askBtn.disabled = false;
      questionInput.focus();
    }
  }

  function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    msgDiv.innerHTML = `
      <div class="message-meta">
        <span class="msg-sender">${role === "user" ? "You" : "DocuRAG AI"}</span>
        <span>${time}</span>
      </div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendAssistantMessage(answer, sources) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message assistant";
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    let citationsHtml = "";
    if (sources && sources.length > 0) {
      citationsHtml = `
        <div class="citations-box">
          <div class="citations-header">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            Verified Source Citations (${sources.length})
          </div>
          <div class="citations-list">
            ${sources
              .map(
                (s, i) => `
              <div class="citation-chip" data-idx="${i}" title="${escapeHtml(s.snippet || '')}">
                <span class="chip-doc">${s.document}</span>
                <span class="chip-page">${s.page ? `P.${s.page}` : "Doc"} [Chunk #${s.chunk_id}]</span>
                <span class="chip-score">${Math.round(s.similarity * 100)}% match</span>
              </div>
            `
              )
              .join("")}
          </div>
        </div>
      `;
    }

    msgDiv.innerHTML = `
      <div class="message-meta">
        <span class="msg-sender">DocuRAG AI</span>
        <span>${time}</span>
      </div>
      <div class="msg-bubble">
        <div class="answer-content">${formatAnswerMarkdown(answer)}</div>
        ${citationsHtml}
        <div class="message-actions">
          <button class="btn-msg-action copy-btn">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>Copy Answer</span>
          </button>
          <button class="btn-msg-action view-ctx-btn">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <span>Inspect Retrieved Context</span>
          </button>
        </div>
      </div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Attach copy event
    const copyBtn = msgDiv.querySelector(".copy-btn");
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(answer);
      copyBtn.querySelector("span").textContent = "Copied!";
      setTimeout(() => {
        copyBtn.querySelector("span").textContent = "Copy Answer";
      }, 2000);
    });

    // Attach View Context button
    const viewCtxBtn = msgDiv.querySelector(".view-ctx-btn");
    viewCtxBtn.addEventListener("click", () => {
      document.getElementById("contextTabBtn").click();
    });

    // Attach citation chip click to view chunk details
    msgDiv.querySelectorAll(".citation-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const idx = parseInt(chip.getAttribute("data-idx"), 10);
        if (sources[idx]) {
          showChunkModal(sources[idx]);
        }
      });
    });
  }

  function appendLoadingMessage() {
    const id = "loading_" + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.className = "message assistant loading";
    msgDiv.id = id;

    msgDiv.innerHTML = `
      <div class="message-meta">
        <span class="msg-sender">DocuRAG AI</span>
        <span>Retrieving...</span>
      </div>
      <div class="msg-bubble" style="display: flex; align-items: center; gap: 10px; color: var(--text-muted);">
        <div class="status-dot" style="animation: pulse 1s infinite alternate;"></div>
        <span>Embedding query, searching ChromaDB & generating grounded response...</span>
      </div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return id;
  }

  function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function clearChat() {
    conversationHistory = [];
    chatMessages.innerHTML = `
      <div class="welcome-card">
        <div class="welcome-header">
          <h2>Conversation Cleared</h2>
          <p>Ready to answer new queries from your indexed documents.</p>
        </div>
      </div>
    `;
  }

  // --- Context & Pipeline Inspectors ---

  function updateContextInspector(query, sources) {
    retrievedCountBadge.textContent = sources.length;
    inspectorSummary.textContent = `Query: "${query.slice(0, 35)}..." &bull; Top-K: ${sources.length} matches`;

    if (!sources || sources.length === 0) {
      retrievedChunksList.innerHTML = `<div class="empty-state"><p>No chunks matched this query.</p></div>`;
      return;
    }

    retrievedChunksList.innerHTML = sources
      .map(
        (chunk, idx) => `
      <div class="chunk-card">
        <div class="chunk-header-row">
          <div class="chunk-meta-tags">
            <span class="chunk-rank">#${idx + 1}</span>
            <span class="chunk-doc">${chunk.document}</span>
            <span class="chunk-page">${chunk.page ? `Page ${chunk.page}` : "Page N/A"}</span>
            <span class="chunk-page">[Chunk ID: ${chunk.chunk_id}]</span>
          </div>
          <div class="chunk-score-badge">
            Cosine Similarity: ${(chunk.similarity * 100).toFixed(1)}% (dist: ${chunk.distance})
          </div>
        </div>
        <div class="chunk-text-preview">${escapeHtml(chunk.snippet || "")}</div>
      </div>
    `
      )
      .join("");
  }

  function updatePipelineInspector(trace) {
    pipelineTotalTime.textContent = `Total Latency: ${trace.total_duration_ms} ms (${trace.llm_provider})`;

    updatePipelineStage(5, "success", `Query embedded & retrieved from ChromaDB`);
    updatePipelineStage(6, "success", `Delimited context constructed`);
    updatePipelineStage(7, "success", `Grounded generation via ${trace.llm_provider}`);
    updatePipelineStage(8, "success", `Source references compiled`);
  }

  function updatePipelineStage(stageNum, status, text) {
    const el = document.getElementById(`stage${stageNum}Status`);
    if (el) {
      el.innerHTML = `<span class="badge-success">${status.toUpperCase()}</span>`;
    }
  }

  function showChunkModal(source) {
    modalTitle.textContent = `${source.document} — Chunk #${source.chunk_id}`;
    modalBody.innerHTML = `
      <div style="margin-bottom: 12px; display: flex; gap: 10px; font-size: 11px;">
        <span style="color: var(--accent-cyan); font-weight: 600;">Relevance: ${Math.round(source.similarity * 100)}%</span>
        <span>Page: ${source.page || "N/A"}</span>
        <span>Distance: ${source.distance}</span>
      </div>
      <div style="background: var(--bg-input); padding: 14px; border-radius: 6px; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; color: #cbd5e1; white-space: pre-wrap;">
        ${escapeHtml(source.snippet || "")}
      </div>
    `;
    docModal.style.display = "flex";
  }

  // --- Utilities ---

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatAnswerMarkdown(text) {
    if (!text) return "";
    let formatted = escapeHtml(text);
    // Bold formatting
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Newlines to line breaks
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
  }
});
