/* ═══════════════════════════════════════
   CEO IDEA INCUBATOR — Frontend Logic
═══════════════════════════════════════ */

let ws = null;
let sessionId = null;
let currentApprovalStep = null;

const AGENT_ICONS = {
  user: '👤', system: '⚙️', groq: '⚡', gemini: '🔷',
  claude: '🟣', planner: '📋', coo: '⚙️', developer: '🏗️',
  designer: '🎨', marketing: '📢', qa: '✅', project_manager: '📊'
};

const AGENT_NAMES = {
  user: 'CEO', system: 'Sistema', groq: 'Groq', gemini: 'Gemini',
  claude: 'Claude', planner: 'Planner', coo: 'COO',
  developer: 'Developer', designer: 'Designer',
  marketing: 'Marketing', qa: 'QA', project_manager: 'Project Manager'
};

// ─────────────────────────────────────
// INIT
// ─────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  startNewSession();
});

async function startNewSession() {
  // Kreiraj sesiju na serveru
  const res = await fetch('/api/session/new', { method: 'POST' });
  const data = await res.json();
  sessionId = data.session_id;

  document.getElementById('sessionInfo').textContent = `Sesija #${sessionId}`;
  document.getElementById('chatMessages').innerHTML = '';

  // Resetuj workflow UI
  resetWorkflow();

  // Otvori WebSocket
  connectWS();
}

function connectWS() {
  if (ws) ws.close();

  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/${sessionId}`);

  ws.onopen = () => {
    setConnStatus(true);
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    handleServerMessage(msg);
  };

  ws.onclose = () => {
    setConnStatus(false);
    // Auto-reconnect nakon 2s
    setTimeout(() => { if (sessionId) connectWS(); }, 2000);
  };

  ws.onerror = () => setConnStatus(false);
}

// ─────────────────────────────────────
// MESSAGE HANDLING
// ─────────────────────────────────────
function handleServerMessage(msg) {
  const { type, content, meta } = msg;

  switch (type) {

    case 'system':
      addMessage('system', content);
      break;

    case 'groq':
      activatePill('groq');
      addMessage('groq', content);
      break;

    case 'gemini':
      activatePill('gemini');
      addMessage('gemini', content);
      break;

    case 'claude':
    case 'planner':
    case 'coo':
    case 'developer':
    case 'designer':
    case 'marketing':
    case 'qa':
    case 'project_manager':
      activatePill('claude');
      addMessage(type, content);
      break;

    case 'agent_start':
      addAgentBanner(content);
      break;

    case 'progress':
      updateProgress(meta.agent, meta.pct, meta.status);
      break;

    case 'approval_request':
      addMessage('system', content);
      showApprovalPanel(meta.step, meta.options);
      break;

    case 'pong':
      break;
  }
}

// ─────────────────────────────────────
// UI: MESSAGES
// ─────────────────────────────────────
function addMessage(type, text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `msg ${type}`;

  const icon = AGENT_ICONS[type] || '🤖';
  const name = AGENT_NAMES[type] || type.toUpperCase();

  div.innerHTML = `
    <div class="msg-avatar">${icon}</div>
    <div class="msg-body">
      <div class="msg-sender">${name}</div>
      <div class="msg-content">${renderMarkdown(text)}</div>
    </div>
  `;

  container.appendChild(div);
  scrollToBottom();
}

function addAgentBanner(text) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = 'agent-banner';
  div.innerHTML = `<div class="dot"></div><span>${text}</span>`;
  container.appendChild(div);
  scrollToBottom();
}

function renderMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^---$/gm, '<hr>')
    .replace(/\n/g, '<br>');
}

function scrollToBottom() {
  const c = document.getElementById('chatMessages');
  c.scrollTop = c.scrollHeight;
}

// ─────────────────────────────────────
// UI: WORKFLOW PROGRESS
// ─────────────────────────────────────
function updateProgress(agent, pct, status) {
  const fill   = document.getElementById(`fill-${agent}`);
  const badge  = document.getElementById(`badge-${agent}`);
  const node   = document.getElementById(`node-${agent}`);
  const statusEl = document.getElementById(`status-${agent}`);

  if (fill)  fill.style.width = `${pct}%`;
  if (badge) badge.textContent = `${pct}%`;

  if (node) {
    node.classList.remove('active', 'done');
    if (status === 'active' || status === 'working') node.classList.add('active');
    if (status === 'done') node.classList.add('done');
  }

  if (statusEl) {
    const labels = { active: 'aktivan', working: 'radi...', done: '✓ gotov', waiting: 'čeka' };
    statusEl.textContent = labels[status] || status;
  }
}

function resetWorkflow() {
  const agents = ['ceo','brainstorm','planner','coo','developer','designer','marketing','qa','project_manager','finale'];
  agents.forEach(a => updateProgress(a, 0, 'waiting'));
}

function focusNode(agent) {
  // Skroluj chat do poruka tog agenta
  const msgs = document.querySelectorAll(`.msg.${agent}`);
  if (msgs.length > 0) {
    msgs[msgs.length - 1].scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// ─────────────────────────────────────
// UI: APPROVAL PANEL
// ─────────────────────────────────────
function showApprovalPanel(step, options) {
  currentApprovalStep = step;
  const panel = document.getElementById('approvalPanel');
  const label = document.getElementById('approvalLabel');
  panel.classList.remove('hidden');

  const labels = {
    'idea_approval': '📋 Sastanak 1 — Da li odobravate ovu verziju ideje?',
    'plan_approval': '📋 Sastanak 2 — Da li odobravate plan realizacije?',
    'mid_review':    '📋 Sastanak 3 — Mid-review: kako nastavljamo?',
    'final_approval':'⭐ Finale — 100% odobravate finalni proizvod?'
  };
  label.textContent = labels[step] || 'Da li nastavljamo?';

  // Sakrij input dok je approval aktivan
  document.getElementById('messageInput').disabled = true;
  document.getElementById('sendBtn').disabled = true;
}

function hideApprovalPanel() {
  document.getElementById('approvalPanel').classList.add('hidden');
  document.getElementById('amendInput').classList.add('hidden');
  document.getElementById('messageInput').disabled = false;
  document.getElementById('sendBtn').disabled = false;
  currentApprovalStep = null;
}

function showAmendInput() {
  document.getElementById('amendInput').classList.remove('hidden');
  document.getElementById('amendText').focus();
}

function sendDecision(decision) {
  const note = decision === 'IZMENI'
    ? document.getElementById('amendText').value.trim()
    : '';

  if (decision === 'IZMENI' && !note) {
    document.getElementById('amendText').focus();
    return;
  }

  // Prikaži CEO odluku u chatu
  const label = { DA: '✅ DA — Nastavljamo!', NE: '❌ NE — Vraćamo na reviziju', IZMENI: `✏️ IZMENI — ${note}` };
  addMessage('user', label[decision] || decision);

  // Pošalji serveru
  wsSend({ type: 'decision', content: decision, note });

  hideApprovalPanel();
}

// ─────────────────────────────────────
// SEND MESSAGE
// ─────────────────────────────────────
function sendMessage() {
  const input = document.getElementById('messageInput');
  const text = input.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

  addMessage('user', text);
  wsSend({ type: 'message', content: text });
  input.value = '';
  input.style.height = 'auto';
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function wsSend(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

// ─────────────────────────────────────
// PILLS
// ─────────────────────────────────────
function activatePill(name) {
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  const pill = document.querySelector(`.pill.${name}`);
  if (pill) pill.classList.add('active');
}

// ─────────────────────────────────────
// CONNECTION STATUS
// ─────────────────────────────────────
function setConnStatus(connected) {
  const dot = document.getElementById('connStatus');
  dot.classList.toggle('active', connected);
  dot.classList.toggle('error', !connected);
  dot.title = connected ? 'Povezan' : 'Nije povezan — pokušavam ponovo...';
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', () => {
  const ta = document.getElementById('messageInput');
  if (ta) {
    ta.addEventListener('input', () => {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    });
  }
});
