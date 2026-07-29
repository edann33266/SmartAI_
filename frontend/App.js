// ---------- Config ----------
const API_BASE = "http://localhost:8000";

// ---------- State ----------
let customers = [];
let selectedCustomerEmail = null;
let lastGeneratedEmail = "";

// ---------- DOM refs ----------
const leadsList = document.getElementById("leadsList");
const leadsEmptyState = document.getElementById("leadsEmptyState");
const sidebarCount = document.getElementById("sidebarCount");
const leadCounter = document.getElementById("leadCounter");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const detailBody = document.getElementById("detailBody");
const generateBtn = document.getElementById("generateBtn");
const sendBtnTop = document.getElementById("sendBtnTop");
const sendBtnBottom = document.getElementById("sendBtnBottom");
const emailContent = document.getElementById("emailContent");
const reasoningContent = document.getElementById("reasoningContent");
const contentValidation = document.getElementById("contentValidation");
const toastStack = document.getElementById("toastStack");

// ---------- Utilities ----------
function setButtonLoading(btn, loading) {
  const spinner = btn.querySelector(".btn-spinner");
  const label = btn.querySelector(".btn-label");
  if (loading) {
    spinner.hidden = false;
    btn.dataset.originalLabel = label.textContent;
    label.textContent = "Processing…";
    btn.disabled = true;
  } else {
    spinner.hidden = true;
    if (btn.dataset.originalLabel) label.textContent = btn.dataset.originalLabel;
  }
}

function showToast(message, type = "info") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  toastStack.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateY(6px)";
    el.style.transition = "opacity 200ms ease, transform 200ms ease";
    setTimeout(() => el.remove(), 220);
  }, 3000);
}

async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  let body = null;
  try { body = await res.json(); } catch (_) { /* no body */ }
  if (!res.ok) {
    const err = new Error((body && (body.detail || body.error)) || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return body;
}

// ---------- Validation ----------
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateEmail(email) {
  if (!email || !email.trim()) return { valid: false, error: "Email address is required" };
  if (!EMAIL_REGEX.test(email.trim())) return { valid: false, error: "Invalid email format" };
  return { valid: true, error: null };
}

function validateEmailContent(text) {
  if (!text || !text.trim()) return { valid: false, error: "Email content cannot be empty" };
  const trimmed = text.trim();
  if (trimmed.length < 10) return { valid: false, error: "Email content is too short (minimum 10 characters)" };
  if (!/subject\s*:/i.test(trimmed)) return { valid: false, error: "Email must include a 'Subject:' line" };
  return { valid: true, error: null };
}

function updateContentValidationFlag() {
  const text = emailContent.value;
  if (!text.trim()) {
    contentValidation.textContent = "";
    contentValidation.className = "validation-flag";
    return;
  }
  const { valid, error } = validateEmailContent(text);
  contentValidation.textContent = valid ? "✓ Valid" : `✗ ${error}`;
  contentValidation.className = `validation-flag ${valid ? "valid" : "invalid"}`;
}

emailContent.addEventListener("input", updateContentValidationFlag);

// ---------- Backend status ----------
async function checkBackendStatus() {
  statusDot.className = "status-dot";
  statusText.textContent = "Checking…";
  try {
    await fetchJson(`${API_BASE}/customers`);
    statusDot.className = "status-dot online";
    statusText.textContent = "Backend online";
    return true;
  } catch (err) {
    statusDot.className = "status-dot offline";
    statusText.textContent = "Backend offline";
    return false;
  }
}

// ---------- Rendering ----------
function renderLeadsList() {
  leadsList.querySelectorAll(".lead-card").forEach((el) => el.remove());
  sidebarCount.textContent = customers.length;
  leadCounter.textContent = `${customers.length} lead${customers.length === 1 ? "" : "s"}`;

  if (customers.length === 0) {
    leadsEmptyState.hidden = false;
    return;
  }
  leadsEmptyState.hidden = true;

  customers.forEach((c) => {
    const card = document.createElement("div");
    card.className = "lead-card" + (c.email === selectedCustomerEmail ? " selected" : "");
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");

    const scoreClass = (c.lead_score ?? 0) >= 80 ? "high" : "mid";
    const selectedFlag = c.selected_for_outreach
      ? `<span class="selected-flag">Selected</span>` : "";

    card.innerHTML = `
      <div class="lead-card-top">
        <span class="lead-name">${escapeHtml(c.name)}</span>
        <span class="lead-score ${scoreClass}">${c.lead_score ?? "—"}</span>
      </div>
      <span class="lead-company">${escapeHtml(c.company || "")}</span>
      ${selectedFlag}
    `;

    card.addEventListener("click", () => selectCustomer(c.email));
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") selectCustomer(c.email);
    });

    leadsList.appendChild(card);
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function renderDetail(customer) {
  if (!customer) {
    detailBody.innerHTML = `
      <div class="empty-state">
        <p>Select a lead to see their profile.</p>
        <span>Pick anyone from the list on the left to get started.</span>
      </div>`;
    return;
  }

  detailBody.innerHTML = `
    <div class="stat-grid">
      <div class="stat-card">
        <span class="stat-label">Name</span>
        <span class="stat-value">${escapeHtml(customer.name)}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Company</span>
        <span class="stat-value">${escapeHtml(customer.company || "—")}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Lead score</span>
        <span class="stat-value">${customer.lead_score ?? "—"}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Last contact</span>
        <span class="stat-value">${customer.last_contact_days_ago ?? customer.contact_days_ago ?? "—"} days ago</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Industry</span>
        <span class="stat-value">${escapeHtml(customer.industry || "—")}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Region</span>
        <span class="stat-value">${escapeHtml(customer.region || "—")}</span>
      </div>
    </div>
  `;
}

// ---------- Actions ----------
async function loadCustomers() {
  try {
    const data = await fetchJson(`${API_BASE}/customers`);
    customers = Array.isArray(data) ? data : [];
    renderLeadsList();
  } catch (err) {
    showToast(`Could not load leads: ${err.message}`, "error");
  }
}

async function selectCustomer(email) {
  selectedCustomerEmail = email;
  renderLeadsList();

  generateBtn.disabled = false;
  sendBtnTop.disabled = true;
  sendBtnBottom.disabled = true;
  emailContent.value = "";
  reasoningContent.value = "";
  contentValidation.textContent = "";

  try {
    const customer = await fetchJson(`${API_BASE}/customers/${encodeURIComponent(email)}`);
    renderDetail(customer);
  } catch (err) {
    if (err.status === 404) {
      showToast(`Customer '${email}' not found`, "error");
      selectedCustomerEmail = null;
      renderDetail(null);
      renderLeadsList();
    } else {
      showToast(`Error loading lead: ${err.message}`, "error");
    }
  }
}

async function handleGenerate() {
  if (!selectedCustomerEmail) {
    showToast("Select a lead first", "warning");
    return;
  }
  const emailValidation = validateEmail(selectedCustomerEmail);
  if (!emailValidation.valid) {
    showToast(emailValidation.error, "error");
    return;
  }

  setButtonLoading(generateBtn, true);
  try {
    const data = await fetchJson(`${API_BASE}/customers/${encodeURIComponent(selectedCustomerEmail)}/generate`, {
      method: "POST",
    });

    const finalEmail = typeof data.final_email === "string" ? data.final_email : String(data.final_email ?? "");
    const reasoning = typeof data.reasoning === "string" ? data.reasoning : String(data.reasoning ?? "");

    emailContent.value = finalEmail;
    reasoningContent.value = reasoning || "No reasoning returned.";
    lastGeneratedEmail = finalEmail;
    updateContentValidationFlag();

    sendBtnTop.disabled = false;
    sendBtnBottom.disabled = false;

    showToast("Email generated successfully", "success");
  } catch (err) {
    if (err.status === 404) {
      showToast("Customer not found", "error");
      selectedCustomerEmail = null;
      renderDetail(null);
      renderLeadsList();
    } else {
      showToast(`Error generating email: ${err.message}`, "error");
    }
  } finally {
    setButtonLoading(generateBtn, false);
  }
}

async function handleSend(triggerBtn) {
  const emailValidation = validateEmail(selectedCustomerEmail);
  if (!emailValidation.valid) {
    showToast(emailValidation.error, "error");
    return;
  }

  const contentValidationResult = validateEmailContent(emailContent.value);
  if (!contentValidationResult.valid) {
    showToast(contentValidationResult.error, "error");
    return;
  }

  const customer = customers.find((c) => c.email === selectedCustomerEmail);
  const name = customer ? customer.name : selectedCustomerEmail;

  const confirmed = window.confirm(`Send this email to ${name}?`);
  if (!confirmed) {
    showToast("Email sending cancelled", "info");
    return;
  }

  setButtonLoading(triggerBtn, true);
  sendBtnTop.disabled = true;
  sendBtnBottom.disabled = true;

  try {
    await fetchJson(`${API_BASE}/customers/${encodeURIComponent(selectedCustomerEmail)}/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email_text: emailContent.value }),
    });
    showToast(`Email sent to ${name}`, "success");
  } catch (err) {
    if (err.status === 404) {
      showToast("Customer not found", "error");
    } else if (err.status === 400) {
      showToast(`Invalid request: ${err.message}`, "error");
    } else {
      showToast(`Failed to send: ${err.message}`, "error");
    }
  } finally {
    setButtonLoading(triggerBtn, false);
    sendBtnTop.disabled = false;
    sendBtnBottom.disabled = false;
  }
}

// ---------- Wiring ----------
generateBtn.addEventListener("click", handleGenerate);
sendBtnTop.addEventListener("click", () => handleSend(sendBtnTop));
sendBtnBottom.addEventListener("click", () => handleSend(sendBtnBottom));

async function init() {
  const online = await checkBackendStatus();
  if (online) await loadCustomers();
  setInterval(checkBackendStatus, 15000);
}

init();
