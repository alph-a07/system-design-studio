/*
  System Design Studio — Interactive Application Engine
  Handles console instruments, installation switchers, syllabus filtering, and clipboard interactions.
*/

// INSTALLATION METHOD TOGGLES
const INSTALL_COMMANDS = {
  curl: {
    command: 'curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/skills/system-design-studio/scripts/init-learning-instance.sh | bash',
    target: 'Target: .system-design/'
  },
  agy: {
    command: 'agy plugin add alph-a07/system-design-studio',
    target: 'Target: Antigravity Customization Engine'
  },
  git: {
    command: 'git clone https://github.com/alph-a07/system-design-studio.git && bash system-design-studio/skills/system-design-studio/scripts/init-learning-instance.sh',
    target: 'Target: Local Clone & Scaffolding'
  }
};

function switchInstallTab(method, buttonEl) {
  const cfg = INSTALL_COMMANDS[method];
  if (!cfg) return;

  const codeEl = document.getElementById('install-command-text');
  const targetEl = document.getElementById('install-target-label');
  if (codeEl) codeEl.textContent = cfg.command;
  if (targetEl) targetEl.textContent = cfg.target;

  const container = buttonEl.closest('.install-tabs');
  if (container) {
    container.querySelectorAll('.install-tab').forEach(btn => btn.classList.remove('active'));
  }
  buttonEl.classList.add('active');
}

// CLIPBOARD COPY
function copySnippet(buttonEl, sourceId) {
  const sourceEl = document.getElementById(sourceId);
  if (!sourceEl) return;

  const textToCopy = sourceEl.textContent.trim();
  navigator.clipboard.writeText(textToCopy).then(() => {
    const originalHtml = buttonEl.innerHTML;
    buttonEl.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <span style="color: #10b981;">Copied!</span>
    `;
    setTimeout(() => {
      buttonEl.innerHTML = originalHtml;
    }, 2000);
  }).catch(() => {
    // Fallback if clipboard permissions blocked
    const input = document.createElement('textarea');
    input.value = textToCopy;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
  });
}

// HERO CONSOLE TAB SWITCHER
function switchConsoleTab(tabKey, buttonEl) {
  const viewCursor = document.getElementById('console-view-cursor');
  const viewTerminal = document.getElementById('console-view-terminal');
  const viewArtifact = document.getElementById('console-view-artifact');

  if (viewCursor) viewCursor.style.display = tabKey === 'cursor' ? 'block' : 'none';
  if (viewTerminal) viewTerminal.style.display = tabKey === 'terminal' ? 'block' : 'none';
  if (viewArtifact) viewArtifact.style.display = tabKey === 'artifact' ? 'block' : 'none';

  const container = buttonEl.closest('.console-nav-tabs');
  if (container) {
    container.querySelectorAll('.console-tab').forEach(tab => tab.classList.remove('active'));
  }
  buttonEl.classList.add('active');
}

// CURRICULUM SYLLABUS RENDERING & FILTERING
let currentActiveTier = 'all';
let currentSearchQuery = '';

function renderCurriculum() {
  const displayEl = document.getElementById('clusters-display');
  const countLabel = document.getElementById('results-count-label');
  if (!displayEl || typeof CURRICULUM_CLUSTERS === 'undefined') return;

  const query = currentSearchQuery.toLowerCase().trim();

  const filteredClusters = CURRICULUM_CLUSTERS.filter(cluster => {
    // Tier filter (code like "0.1", "1.4", "2.3")
    const tierMatch = currentActiveTier === 'all' || cluster.code.startsWith(currentActiveTier + '.');

    // Search query filter
    if (!query) return tierMatch;

    const inTitle = cluster.title.toLowerCase().includes(query);
    const inCode = cluster.code.toLowerCase().includes(query);
    const inTopics = cluster.topics.some(t => t.title.toLowerCase().includes(query) || t.id.toLowerCase().includes(query));

    return tierMatch && (inTitle || inCode || inTopics);
  });

  const totalTopics = filteredClusters.reduce((acc, c) => acc + c.topics.length, 0);

  if (countLabel) {
    countLabel.textContent = `Showing ${filteredClusters.length} of ${CURRICULUM_CLUSTERS.length} clusters (${totalTopics} topics)`;
  }

  if (filteredClusters.length === 0) {
    displayEl.innerHTML = `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-wire); border-radius: var(--radius-md); padding: 36px; text-align: center;">
        <p style="font-size: 15px; color: var(--text-secondary); margin-bottom: 8px;">No matching clusters or topics found.</p>
        <p style="font-size: 13px; color: var(--text-muted);">Try a broader search query or switch tier filter.</p>
      </div>
    `;
    return;
  }

  displayEl.innerHTML = filteredClusters.map(cluster => {
    const topicsHtml = cluster.topics.map(topic => `
      <div class="topic-row">
        <span class="topic-id-tag">${topic.id.replace('topic.', '')}</span>
        <span class="topic-name">${topic.title}</span>
      </div>
    `).join('');

    return `
      <article class="cluster-block" id="cluster-${cluster.code}">
        <div class="cluster-block-header">
          <div class="cluster-title-wrap">
            <span class="cluster-code-badge">${cluster.code}</span>
            <h2 class="cluster-title-text">${cluster.title.replace(/^([0-9]+\.\s*\[[0-9.]+\]\s*)/, '')}</h2>
          </div>
          <span class="cluster-topic-count">${cluster.topics.length} topics</span>
        </div>
        <div class="topics-grid">
          ${topicsHtml}
        </div>
      </article>
    `;
  }).join('');
}

function filterByTier(tierKey, buttonEl) {
  currentActiveTier = tierKey;
  const container = document.getElementById('tier-filters');
  if (container) {
    container.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
  }
  if (buttonEl) buttonEl.classList.add('active');
  renderCurriculum();
}

function handleCurriculumSearch(query) {
  currentSearchQuery = query;
  renderCurriculum();
}

// INITIALIZATION ON DOM READY
document.addEventListener('DOMContentLoaded', () => {
  // Check if curriculum page and URL contains ?tier=
  if (document.getElementById('clusters-display')) {
    const params = new URLSearchParams(window.location.search);
    const tierParam = params.get('tier');
    if (tierParam && ['0', '1', '2', '3', '4', '5'].includes(tierParam)) {
      currentActiveTier = tierParam;
      const targetBtn = document.querySelector(`.filter-pill[data-tier="${tierParam}"]`);
      if (targetBtn) {
        document.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
        targetBtn.classList.add('active');
      }
    }
    renderCurriculum();
  }
});
