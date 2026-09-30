/**
 * Google Photos AI Discovery Engine & Retrieval MVP — Interactive Dashboard App
 */

let state = {
  activeTab: 'overview',
  overviewData: null,
  failuresData: [],
  cluesData: null,
  personasData: null,
  charts: {}
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  loadOverviewData();
  checkLlmStatus();
});

// Navigation Handler
function initNavigation() {
  const links = document.querySelectorAll('.nav-link');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      switchTab(targetTab);
      if (window.innerWidth <= 768) {
        closeMobileSidebar();
      }
    });
  });
}

// Mobile Sidebar Toggle
function toggleMobileSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  const isOpen = sidebar.classList.contains('sidebar-open');
  if (isOpen) {
    closeMobileSidebar();
  } else {
    sidebar.classList.add('sidebar-open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeMobileSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  if (sidebar) sidebar.classList.remove('sidebar-open');
  if (overlay) overlay.classList.remove('active');
  document.body.style.overflow = '';
}

function switchTab(tabId) {
  state.activeTab = tabId;
  
  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-tab') === tabId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Update tab panes
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.remove('active');
  });
  
  const targetPane = document.getElementById(`tab-${tabId}`);
  if (targetPane) {
    targetPane.classList.add('active');
  }

  // Update Top Bar Title
  const titles = {
    overview: 'Discovery Engine Overview & Metric Funnel',
    failures: 'Ranked Retrieval Failure Modes',
    clues: 'Cognitive Memory: Clues Remembered vs Forgotten',
    personas: 'Target User Personas Breakdown',
    discovery: 'AI Discovery Engine Copilot',
    mvp: 'Part 5: AI-Native Retrieval MVP Prototype'
  };
  const titleEl = document.getElementById('top-bar-title');
  if (titleEl) titleEl.innerText = titles[tabId] || 'Dashboard';

  // Load Tab Specific Data
  if (tabId === 'failures' && state.failuresData.length === 0) {
    loadFailuresData();
  } else if (tabId === 'clues' && !state.cluesData) {
    loadCluesData();
  } else if (tabId === 'personas' && !state.personasData) {
    loadPersonasData();
  } else if (tabId === 'mvp') {
    // Run an initial search to populate candidate results
    const input = document.getElementById('mvp-search-input');
    if (input && input.value) {
      executeMvpSearch();
    }
  }
}

// ──────────────────────────────────────────────
// Overview Tab
// ──────────────────────────────────────────────
async function loadOverviewData() {
  try {
    const res = await fetch('/api/overview');
    const json = await res.json();
    if (json.status !== 'success') return;

    const data = json.data;
    state.overviewData = data;

    // Update Hero Stats
    const stats = data.stats || {};
    const totalDocsEl = document.getElementById('stat-total-docs');
    const totalExtsEl = document.getElementById('stat-total-extractions');
    const avgConfEl = document.getElementById('stat-avg-conf');

    if (totalDocsEl) totalDocsEl.innerText = (stats.total_documents || 0).toLocaleString();
    if (totalExtsEl) totalExtsEl.innerText = (stats.total_extractions || 0).toLocaleString();
    if (avgConfEl) avgConfEl.innerText = `${((stats.avg_confidence || 0) * 100).toFixed(1)}%`;

    // Render Overview Charts
    renderOverviewFailuresChart(data.topFailures || data.topBlockers || []);
    renderOverviewCategoriesChart(data.photoCategories || {});
  } catch (err) {
    console.error('Error loading overview data:', err);
  }
}

function renderOverviewFailuresChart(failures) {
  const ctx = document.getElementById('overview-failures-chart');
  if (!ctx) return;

  if (state.charts['overview-failures']) {
    state.charts['overview-failures'].destroy();
  }

  const labels = failures.slice(0, 5).map(f => (f.failure_tag || f.blocker_tag || '').replace(/_/g, ' '));
  const counts = failures.slice(0, 5).map(f => f.occurrence_count || 0);

  state.charts['overview-failures'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'User Reports',
        data: counts,
        backgroundColor: [
          '#1a73e8',
          '#ea4335',
          '#fbbc04',
          '#34a853',
          '#8ab4f8'
        ],
        borderRadius: 8
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9aa0b4' }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#f3f4f8', font: { family: 'Outfit', size: 12 } }
        }
      }
    }
  });
}

function renderOverviewCategoriesChart(categories) {
  const ctx = document.getElementById('overview-categories-chart');
  if (!ctx) return;

  if (state.charts['overview-categories']) {
    state.charts['overview-categories'].destroy();
  }

  const labels = Object.keys(categories).map(k => k.replace(/_/g, ' '));
  const data = Object.values(categories);

  state.charts['overview-categories'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#1a73e8',
          '#ea4335',
          '#fbbc04',
          '#34a853',
          '#a855f7'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#9aa0b4', font: { family: 'Plus Jakarta Sans', size: 12 }, padding: 12 }
        }
      },
      cutout: '68%'
    }
  });
}

// ──────────────────────────────────────────────
// Retrieval Failures Tab
// ──────────────────────────────────────────────
async function loadFailuresData() {
  const container = document.getElementById('failures-list-container');
  if (!container) return;

  try {
    const res = await fetch('/api/failures');
    const json = await res.json();
    if (json.status !== 'success') return;

    state.failuresData = json.data;
    renderFailuresList(json.data);
  } catch (err) {
    container.innerHTML = '<div class="error-msg">Failed to load failure points.</div>';
  }
}

function renderFailuresList(failures) {
  const container = document.getElementById('failures-list-container');
  if (!container) return;

  if (!failures || failures.length === 0) {
    container.innerHTML = '<div class="empty-state">No failure modes recorded.</div>';
    return;
  }

  let html = '';
  failures.forEach((f, idx) => {
    const tag = (f.failure_tag || f.blocker_tag || '').replace(/_/g, ' ');
    const count = f.occurrence_count || 0;
    const conf = Math.round((f.avg_confidence || 0.8) * 100);
    const samples = f.sample_texts || [];

    html += `
      <div class="evidence-card">
        <div class="evidence-header">
          <div class="tag-title">
            <span class="rank-badge">#${idx + 1}</span>
            <span class="failure-title-text">${tag}</span>
          </div>
          <div class="metric-chips">
            <span class="metric-chip">${count} Customer Reports</span>
            <span class="metric-chip conf-chip">${conf}% Confidence</span>
          </div>
        </div>
        <div class="evidence-quotes">
          ${samples.slice(0, 3).map(quote => `
            <div class="quote-item">
              <span class="quote-icon">“</span>
              <p class="quote-text">${quote}</p>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// ──────────────────────────────────────────────
// Memory Clues vs Forgotten Tab
// ──────────────────────────────────────────────
async function loadCluesData() {
  try {
    const res = await fetch('/api/clues');
    const json = await res.json();
    if (json.status !== 'success') return;

    state.cluesData = json.data;
    renderCluesCharts(json.data);
  } catch (err) {
    console.error('Error loading clues data:', err);
  }
}

function renderCluesCharts(data) {
  // Chart 1: What Users Remember
  const ctxRem = document.getElementById('remembered-clues-chart');
  if (ctxRem) {
    if (state.charts['remembered-clues']) state.charts['remembered-clues'].destroy();

    const remLabels = Object.keys(data.rememberedClues || {}).map(k => k.replace(/_/g, ' '));
    const remValues = Object.values(data.rememberedClues || {});

    state.charts['remembered-clues'] = new Chart(ctxRem, {
      type: 'bar',
      data: {
        labels: remLabels,
        datasets: [{
          label: 'Frequency Retained',
          data: remValues,
          backgroundColor: '#1a73e8',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9aa0b4' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9aa0b4' } }
        }
      }
    });
  }

  // Chart 2: What Users Forget
  const ctxForg = document.getElementById('forgotten-elements-chart');
  if (ctxForg) {
    if (state.charts['forgotten-elements']) state.charts['forgotten-elements'].destroy();

    const forgLabels = Object.keys(data.forgottenElements || {}).map(k => k.replace(/_/g, ' '));
    const forgValues = Object.values(data.forgottenElements || {});

    state.charts['forgotten-elements'] = new Chart(ctxForg, {
      type: 'bar',
      data: {
        labels: forgLabels,
        datasets: [{
          label: 'Frequency Forgotten',
          data: forgValues,
          backgroundColor: '#ea4335',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9aa0b4' } },
          y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9aa0b4' } }
        }
      }
    });
  }
}

// ──────────────────────────────────────────────
// Personas Tab
// ──────────────────────────────────────────────
async function loadPersonasData() {
  const container = document.getElementById('personas-cards-container');
  if (!container) return;

  try {
    const res = await fetch('/api/personas');
    const json = await res.json();
    if (json.status !== 'success') return;

    state.personasData = json.data;
    renderPersonas(json.data);
  } catch (err) {
    container.innerHTML = '<div class="error-msg">Failed to load personas.</div>';
  }
}

function renderPersonas(data) {
  const container = document.getElementById('personas-cards-container');
  if (!container) return;

  const personaDescriptions = {
    life_documenter: {
      title: 'The Life Documenter',
      subtitle: '25,000+ photos, heavy daily capture',
      desc: 'Takes hundreds of photos per trip and casual day. Suffers the most from unranked search overload and 20-minute timeline scroll fatigue.',
      icon: '📸'
    },
    visual_note_taker: {
      title: 'The Visual Note-Taker',
      subtitle: 'Uses camera as external memory',
      desc: 'Snaps medicine strips, receipts, warranty serial numbers, parking tickets. Struggles when OCR fails to index blurry or shiny foil text.',
      icon: '📝'
    },
    nostalgia_seeker: {
      title: 'The Nostalgia Seeker',
      subtitle: 'Emotional archivist (5–10 years)',
      desc: 'Searches for deep personal memories from college days or deceased family members. Cannot recall exact years; faces broken archive jumps.',
      icon: '🕰️'
    },
    screenshot_curator: {
      title: 'The Screenshot Curator',
      subtitle: 'Thousands of unindexed screenshots',
      desc: 'Saves book recommendations, recipes, and Twitter threads. Search fails because visual screenshot context and app UI are completely unindexed.',
      icon: '📱'
    },
    family_archivist: {
      title: 'The Family Archivist',
      subtitle: 'Preserving family & children milestones',
      desc: 'Tracks kids growing up, school performances, and family holidays. Desperately wants expression/mood filters like "funny messy meal".',
      icon: '👨‍👩‍👧'
    }
  };

  const personas = data.personas || [];
  let html = '';

  personas.forEach(p => {
    const rawKey = p.user_persona || p.shopper_persona || '';
    const meta = personaDescriptions[rawKey] || {
      title: rawKey.replace(/_/g, ' ').toUpperCase(),
      subtitle: 'Photo Search User',
      desc: 'Discovered behavioral cohort in Google Photos.',
      icon: '👤'
    };

    html += `
      <div class="persona-card">
        <div class="persona-header">
          <span class="persona-icon">${meta.icon}</span>
          <div>
            <h4>${meta.title}</h4>
            <span class="persona-sub">${meta.subtitle}</span>
          </div>
          <div class="persona-count">${p.count} Reports</div>
        </div>
        <p class="persona-desc">${meta.desc}</p>
        <div class="persona-stat-row">
          <span>Signal Confidence:</span>
          <strong>${Math.round((p.avg_conf || 0.8) * 100)}%</strong>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

// ──────────────────────────────────────────────
// Discovery Engine Q&A Copilot
// ──────────────────────────────────────────────
async function checkLlmStatus() {
  const chip = document.getElementById('llm-connection-chip');
  if (!chip) return;

  try {
    const res = await fetch('/api/llm-status');
    const json = await res.json();
    if (json.connected) {
      chip.innerText = `Connected (${json.active_model})`;
      chip.style.borderColor = 'rgba(52, 168, 83, 0.4)';
      chip.style.color = '#34a853';
    } else {
      chip.innerText = 'Offline Fallback Ready';
      chip.style.borderColor = 'rgba(251, 188, 4, 0.4)';
      chip.style.color = '#fbbc04';
    }
  } catch (e) {
    chip.innerText = 'Offline Fallback Ready';
  }
}

function askPresetQuestion(question) {
  const input = document.getElementById('chat-input');
  if (input) {
    input.value = question;
    sendUserQuestion();
  }
}

async function sendUserQuestion() {
  const input = document.getElementById('chat-input');
  const history = document.getElementById('chat-history-container');
  const btn = document.getElementById('btn-send-chat');

  if (!input || !input.value.trim()) return;
  const question = input.value.trim();

  // Append user message
  const userMsgHtml = `
    <div class="chat-message user-message">
      <div class="message-badge">Product Fellow</div>
      <div class="message-content">${question}</div>
    </div>
  `;
  history.innerHTML += userMsgHtml;
  input.value = '';

  // Append loading placeholder
  const loadingId = `loading-${Date.now()}`;
  history.innerHTML += `
    <div class="chat-message assistant-message" id="${loadingId}">
      <div class="message-badge">Google Photos PM Copilot</div>
      <div class="message-content">
        <em>Analyzing research database and synthesizing evidence...</em>
      </div>
    </div>
  `;
  history.scrollTop = history.scrollHeight;

  btn.disabled = true;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const json = await res.json();

    const loadingEl = document.getElementById(loadingId);
    if (loadingEl && json.status === 'success') {
      const parsedMarkdown = marked.parse(json.data.answer);
      loadingEl.innerHTML = `
        <div class="message-badge">Google Photos PM Copilot (${json.data.model_used})</div>
        <div class="message-content">${parsedMarkdown}</div>
      `;
    } else if (loadingEl) {
      loadingEl.innerHTML = `<div class="error-msg">Failed to generate answer.</div>`;
    }
  } catch (err) {
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    history.scrollTop = history.scrollHeight;
  }
}

// ──────────────────────────────────────────────
// Part 5: AI-Native Retrieval MVP Prototype
// ──────────────────────────────────────────────
function setMvpQuery(q) {
  const input = document.getElementById('mvp-search-input');
  if (input) {
    input.value = q;
    executeMvpSearch();
  }
}

async function executeMvpSearch() {
  const input = document.getElementById('mvp-search-input');
  const grid = document.getElementById('mvp-results-grid');
  const countEl = document.getElementById('mvp-match-count');

  if (!input || !input.value.trim()) return;
  const query = input.value.trim();

  grid.innerHTML = '<div class="mvp-empty-state"><p>Running associative memory search across photo candidate library...</p></div>';
  if (countEl) countEl.innerText = 'Searching...';

  try {
    const res = await fetch('/api/retrieval-mvp/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const json = await res.json();

    if (json.status !== 'success' || !json.results || json.results.length === 0) {
      grid.innerHTML = `
        <div class="mvp-empty-state">
          <p>No high-confidence matches found in sample album for: "${query}". Try one of the real test scenario chips above!</p>
        </div>
      `;
      if (countEl) countEl.innerText = '0 matches';
      return;
    }

    if (countEl) countEl.innerText = `${json.matches_found} candidate photos retrieved`;

    let html = '';
    json.results.forEach(item => {
      const p = item.photo;
      const confPct = Math.round(item.confidence_score * 100);

      html += `
        <div class="mvp-photo-card">
          <div class="mvp-photo-img-wrap">
            <img src="${p.image_url}" alt="${p.title}" class="mvp-photo-img" loading="lazy">
            <span class="mvp-confidence-pill">${confPct}% Match Confidence</span>
          </div>
          <div class="mvp-photo-info">
            <h4 class="mvp-photo-title">${p.title}</h4>
            <div class="mvp-meta-row">
              <span>📅 ${p.approx_date}</span>
              ${p.companion !== 'None' ? `<span>👥 With: ${p.companion}</span>` : ''}
            </div>
            <div class="clues-tags-wrap">
              ${item.matched_clues.map(c => `<span class="clue-badge">${c}</span>`).join('')}
            </div>
            <div class="mvp-reasoning">
              <strong>Associative Match:</strong> ${item.retrieval_reasoning}
            </div>
          </div>
        </div>
      `;
    });

    grid.innerHTML = html;
  } catch (err) {
    grid.innerHTML = `<div class="error-msg">Search error: ${err.message}</div>`;
  }
}
