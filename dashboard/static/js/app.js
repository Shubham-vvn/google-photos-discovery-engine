/**
 * Myntra Discovery Engine — Interactive Dashboard App
 */

let state = {
  activeTab: 'overview',
  overviewData: null,
  blockersData: [],
  uncertaintiesData: null,
  personasData: null,
  charts: {}
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  loadOverviewData();
});

// Navigation Handler
function initNavigation() {
  const links = document.querySelectorAll('.nav-link');
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      switchTab(targetTab);
      // Close sidebar on mobile after navigation
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
  sidebar.classList.remove('sidebar-open');
  overlay.classList.remove('active');
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
    overview: 'Discovery Engine Overview',
    blockers: 'Conversion Blockers Analysis',
    uncertainties: 'Customer Uncertainty Matrix',
    personas: 'Shopper Personas Breakdown',
    discovery: 'AI Discovery Engine'
  };
  const titleEl = document.getElementById('top-bar-title');
  if (titleEl) titleEl.innerText = titles[tabId] || 'Dashboard';

  // Load Tab Specific Data
  if (tabId === 'blockers' && state.blockersData.length === 0) {
    loadBlockersData();
  } else if (tabId === 'uncertainties' && !state.uncertaintiesData) {
    loadUncertaintiesData();
  } else if (tabId === 'personas' && !state.personasData) {
    loadPersonasData();
  } else if (tabId === 'discovery') {
    initDiscoveryTab();
  }
}

// ──────────────────────────────────────────────
// 1. Overview Tab
// ──────────────────────────────────────────────
async function loadOverviewData() {
  try {
    const res = await fetch('/api/overview');
    const json = await res.json();
    if (json.status === 'success') {
      state.overviewData = json.data;
      renderOverviewStats(json.data.stats);
      renderOverviewCharts(json.data);
      renderRecentFeed(json.data.topBlockers);
    }
  } catch (err) {
    console.error('Failed to load overview data:', err);
  }
}

function renderOverviewStats(stats) {
  document.getElementById('stat-total-docs').innerText = stats.total_documents || 0;
  document.getElementById('stat-total-extractions').innerText = stats.total_extractions || 0;
  document.getElementById('stat-avg-conf').innerText = (stats.avg_confidence * 100).toFixed(1) + '%';
  
  const sourcesText = Object.entries(stats.sources || {})
    .map(([src, count]) => `${src}: ${count}`)
    .join(' | ') || 'Google Play Store';
  document.getElementById('stat-sources').innerText = sourcesText;
}

function renderOverviewCharts(data) {
  // Chart 1: Top Blockers Bar Chart
  const ctxBlockers = document.getElementById('chart-top-blockers');
  if (ctxBlockers) {
    if (state.charts.blockers) state.charts.blockers.destroy();
    
    const blockers = data.topBlockers || [];
    const labels = blockers.map(b => b.blocker_tag.replace(/_/g, ' '));
    const counts = blockers.map(b => b.occurrence_count);
    const weighted = blockers.map(b => b.weighted_count);

    state.charts.blockers = new Chart(ctxBlockers, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Weighted Impact',
            data: weighted,
            backgroundColor: 'rgba(99, 102, 241, 0.85)',
            borderRadius: 6,
          },
          {
            label: 'Raw Count',
            data: counts,
            backgroundColor: 'rgba(168, 85, 247, 0.4)',
            borderRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#9aa0b4', font: { family: 'Plus Jakarta Sans' } } }
        },
        scales: {
          x: { ticks: { color: '#9aa0b4', font: { family: 'Plus Jakarta Sans', size: 11 } }, grid: { display: false } },
          y: { ticks: { color: '#9aa0b4' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }

  // Chart 2: Confidence Distribution Donut
  const ctxConf = document.getElementById('chart-confidence-dist');
  if (ctxConf) {
    if (state.charts.confidence) state.charts.confidence.destroy();
    
    const confDist = data.confidenceDistribution || {};
    state.charts.confidence = new Chart(ctxConf, {
      type: 'doughnut',
      data: {
        labels: ['High (0.7-1.0)', 'Medium (0.4-0.7)', 'Low (0.0-0.4)'],
        datasets: [{
          data: [
            confDist['high (0.7-1.0)'] || 0,
            confDist['medium (0.4-0.7)'] || 0,
            confDist['low (0.0-0.4)'] || 0
          ],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#9aa0b4', font: { family: 'Plus Jakarta Sans', size: 11 } } }
        },
        cutout: '70%'
      }
    });
  }
}

function renderRecentFeed(topBlockers) {
  const container = document.getElementById('recent-feed-container');
  if (!container) return;

  if (!topBlockers || topBlockers.length === 0) {
    container.innerHTML = '<p class="stat-desc">No blocker patterns generated yet.</p>';
    return;
  }

  container.innerHTML = topBlockers.map((b, i) => `
    <div class="blocker-card" style="margin-bottom: 12px; padding: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span class="blocker-rank">${i+1}</span>
          <span style="font-weight: 700; color: #fff; text-transform: capitalize;">${b.blocker_tag.replace(/_/g, ' ')}</span>
        </div>
        <span class="badge badge-high">${(b.avg_confidence * 100).toFixed(0)}% Confidence</span>
      </div>
    </div>
  `).join('');
}

// ──────────────────────────────────────────────
// 2. Purchase Blockers Tab
// ──────────────────────────────────────────────
async function loadBlockersData() {
  const container = document.getElementById('blockers-list-container');
  container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">Loading blocker analysis...</p>';

  try {
    const res = await fetch('/api/blockers');
    const json = await res.json();
    if (json.status === 'success') {
      state.blockersData = json.data;
      renderBlockersList(json.data);
    }
  } catch (err) {
    console.error('Failed to load blockers:', err);
  }
}

function renderBlockersList(blockers) {
  const container = document.getElementById('blockers-list-container');
  if (!blockers || blockers.length === 0) {
    container.innerHTML = '<p style="color: var(--text-secondary);">No blockers extracted yet.</p>';
    return;
  }

  container.innerHTML = blockers.map((b, i) => {
    const quotes = b.sample_texts || [];
    const confClass = b.avg_confidence >= 0.7 ? 'badge-high' : b.avg_confidence >= 0.4 ? 'badge-med' : 'badge-low';
    
    return `
      <div class="blocker-card">
        <div class="blocker-top">
          <div class="blocker-tag-title">
            <div class="blocker-rank">${i + 1}</div>
            <div>
              <div class="blocker-name">${b.blocker_tag.replace(/_/g, ' ')}</div>
              <span class="stat-desc">Identified across ${b.occurrence_count} customer reviews</span>
            </div>
          </div>
          <div class="metrics-pills">
            <span class="badge badge-neutral">Weighted Impact: <strong>${b.weighted_count}</strong></span>
            <span class="badge ${confClass}">${(b.avg_confidence * 100).toFixed(0)}% Confidence</span>
          </div>
        </div>

        ${quotes.length > 0 ? `
          <div style="margin-top: 14px;">
            <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); font-weight: 700;">Customer Voice Evidence:</span>
            ${quotes.slice(0, 2).map(q => `
              <div class="quote-box">"${q}"</div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }).join('');
}

// ──────────────────────────────────────────────
// 3. Uncertainties Tab
// ──────────────────────────────────────────────
async function loadUncertaintiesData() {
  try {
    const res = await fetch('/api/uncertainties');
    const json = await res.json();
    if (json.status === 'success') {
      state.uncertaintiesData = json.data;
      renderUncertaintiesRadar(json.data.distribution);
    }
  } catch (err) {
    console.error('Failed to load uncertainties:', err);
  }
}

function renderUncertaintiesRadar(dist) {
  const ctx = document.getElementById('chart-uncertainty-radar');
  if (!ctx) return;

  if (state.charts.radar) state.charts.radar.destroy();

  const labels = Object.keys(dist || {}).map(k => k.toUpperCase());
  const counts = Object.values(dist || {});

  state.charts.radar = new Chart(ctx, {
    type: 'polarArea',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: [
          'rgba(99, 102, 241, 0.7)',
          'rgba(255, 63, 108, 0.7)',
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(6, 182, 212, 0.7)'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          ticks: { color: '#9aa0b4', backdropColor: 'transparent' },
          grid: { color: 'rgba(255,255,255,0.06)' }
        }
      },
      plugins: {
        legend: { position: 'right', labels: { color: '#9aa0b4', font: { family: 'Plus Jakarta Sans' } } }
      }
    }
  });
}

// ──────────────────────────────────────────────
// 4. Personas Tab
// ──────────────────────────────────────────────
async function loadPersonasData() {
  try {
    const res = await fetch('/api/personas');
    const json = await res.json();
    if (json.status === 'success') {
      state.personasData = json.data;
      renderPersonaCards(json.data.personas);
      renderCrosstabTable(json.data.crosstab);
    }
  } catch (err) {
    console.error('Failed to load personas:', err);
  }
}

function renderPersonaCards(personas) {
  const container = document.getElementById('persona-cards-container');
  if (!container) return;

  container.innerHTML = (personas || []).map(p => `
    <div class="stat-card">
      <div class="stat-header">
        <span class="stat-title">${p.shopper_persona.replace(/_/g, ' ')}</span>
        <div class="stat-icon-badge stat-icon-purple">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
      </div>
      <div class="stat-value">${p.count}</div>
      <div class="stat-desc">Avg Confidence: ${(p.avg_conf * 100).toFixed(0)}%</div>
    </div>
  `).join('');
}

function renderCrosstabTable(crosstab) {
  const container = document.getElementById('crosstab-container');
  if (!container) return;

  const rows = [];
  Object.entries(crosstab || {}).forEach(([persona, blockers]) => {
    blockers.forEach(b => {
      rows.push(`
        <tr>
          <td style="font-weight: 700; color: #fff; text-transform: capitalize;">${persona.replace(/_/g, ' ')}</td>
          <td style="color: var(--accent-primary); font-weight: 600; text-transform: capitalize;">${b.blocker.replace(/_/g, ' ')}</td>
          <td style="font-weight: 600;">${b.count}</td>
          <td><span class="badge badge-high">${(b.avg_confidence * 100).toFixed(0)}%</span></td>
        </tr>
      `);
    });
  });

  container.innerHTML = `
    <table class="crosstab-table">
      <thead>
        <tr>
          <th>Shopper Persona</th>
          <th>Top Conversion Blocker</th>
          <th>Frequency</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        ${rows.join('') || '<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No cross-tabulated records found</td></tr>'}
      </tbody>
    </table>
  `;
}



// ──────────────────────────────────────────────
// 6. AI Discovery Engine Tab
// ──────────────────────────────────────────────
let discoveryInitialized = false;

function initDiscoveryTab() {
  if (discoveryInitialized) return;
  discoveryInitialized = true;

  // Chip click handlers
  document.querySelectorAll('.discovery-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const question = chip.getAttribute('data-question');
      const input = document.getElementById('discovery-question-input');
      if (input) {
        input.value = question;
        askDiscoveryEngine();
      }
    });
  });

  // Enter key handler
  const input = document.getElementById('discovery-question-input');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        askDiscoveryEngine();
      }
    });
  }
}

async function askDiscoveryEngine() {
  const input = document.getElementById('discovery-question-input');
  const askBtn = document.getElementById('discovery-ask-btn');
  const loadingEl = document.getElementById('discovery-loading');
  const answerArea = document.getElementById('discovery-answer-area');
  const evidenceSection = document.getElementById('discovery-evidence-section');

  const question = input?.value?.trim();
  if (!question) return;

  // Show loading, hide previous results
  loadingEl.style.display = 'flex';
  answerArea.style.display = 'none';
  evidenceSection.style.display = 'none';
  askBtn.disabled = true;

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    const json = await res.json();

    if (json.status === 'success' && json.data) {
      renderDiscoveryAnswer(json.data);
    } else {
      renderDiscoveryAnswer({
        answer: '❌ **Unexpected Error**\n\nSomething went wrong while processing your question. Please try again.',
        source_type: 'not_found',
        evidence_used: [],
        confidence: 0,
      });
    }
  } catch (err) {
    console.error('Discovery Engine error:', err);
    renderDiscoveryAnswer({
      answer: '❌ **Connection Error**\n\nCould not reach the AI Discovery Engine. Please check that the server is running and try again.',
      source_type: 'not_found',
      evidence_used: [],
      confidence: 0,
    });
  } finally {
    loadingEl.style.display = 'none';
    askBtn.disabled = false;
  }
}

function renderDiscoveryAnswer(data) {
  const answerArea = document.getElementById('discovery-answer-area');
  const sourceBadge = document.getElementById('discovery-source-badge');
  const answerContent = document.getElementById('discovery-answer-content');
  const evidenceSection = document.getElementById('discovery-evidence-section');
  const evidenceGrid = document.getElementById('discovery-evidence-grid');

  // Source badge
  const sourceConfig = {
    research: {
      text: '📊 Answered from Research Data',
      className: 'source-research',
    },
    llm: {
      text: '🤖 Answered by AI (General Knowledge)',
      className: 'source-llm',
    },
    not_found: {
      text: '⚠️ Limited or No Data Available',
      className: 'source-not-found',
    }
  };

  const config = sourceConfig[data.source_type] || sourceConfig.not_found;
  sourceBadge.textContent = config.text;
  sourceBadge.className = `discovery-source-badge ${config.className}`;

  // Render markdown answer
  let renderedHtml = '';
  if (typeof marked !== 'undefined' && marked.parse) {
    renderedHtml = marked.parse(data.answer || '');
  } else {
    // Fallback: basic formatting
    renderedHtml = (data.answer || '')
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  }

  answerContent.innerHTML = renderedHtml;

  // Add stats pills if available
  if (data.stats) {
    const statsHtml = `
      <div class="discovery-stats-pills">
        <span class="discovery-stats-pill">📄 <strong>${data.stats.extractions_matched || 0}</strong> evidence records matched</span>
        <span class="discovery-stats-pill">🚧 <strong>${data.stats.blockers_available || 0}</strong> blockers analyzed</span>
        <span class="discovery-stats-pill">👥 <strong>${data.stats.personas_available || 0}</strong> personas identified</span>
        ${data.confidence ? `<span class="discovery-stats-pill">🎯 Avg confidence: <strong>${(data.confidence * 100).toFixed(0)}%</strong></span>` : ''}
      </div>
    `;
    answerContent.innerHTML += statsHtml;
  }

  // Show the answer area with animation
  answerArea.style.display = 'block';

  // Evidence cards (only for research-backed answers)
  if (data.source_type === 'research' && data.evidence_used && data.evidence_used.length > 0) {
    evidenceGrid.innerHTML = data.evidence_used.map(ev => {
      const confClass = ev.confidence >= 0.7 ? 'badge-high' : ev.confidence >= 0.4 ? 'badge-med' : 'badge-low';
      return `
        <div class="evidence-card">
          <div>
            <div class="evidence-header">
              <span class="source-tag">${ev.source || 'UNKNOWN'}</span>
              <span class="badge ${confClass}">${(ev.confidence * 100).toFixed(0)}% Conf</span>
            </div>
            <p class="evidence-text">"${ev.text}"</p>
          </div>
          <div class="evidence-footer">
            <div>
              <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase;">Blocker:</div>
              <div style="font-size: 12.5px; font-weight: 700; color: #fff;">${ev.blocker ? ev.blocker.replace(/_/g, ' ') : 'N/A'}</div>
            </div>
            <span class="persona-tag">${ev.persona ? ev.persona.replace(/_/g, ' ') : ''}</span>
          </div>
        </div>
      `;
    }).join('');
    evidenceSection.style.display = 'block';
  } else {
    evidenceSection.style.display = 'none';
  }
}
