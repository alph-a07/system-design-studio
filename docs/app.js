/*
  System Design Studio — Interactive Application Engine
  Handles console instruments, installation switchers, syllabus filtering,
  and browser-storage persisted progress tracking.
*/

// STORAGE KEY
const PROGRESS_STORAGE_KEY = 'sds_mastered_topics';

// SAFE LOCAL STORAGE WRAPPERS
function getMasteredTopicIds() {
  try {
    const raw = localStorage.getItem(PROGRESS_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? new Set(parsed) : new Set();
  } catch (err) {
    console.warn('[SDS] Local storage not accessible; using session memory.', err);
    return new Set();
  }
}

function saveMasteredTopicIds(topicSet) {
  try {
    const arr = Array.from(topicSet);
    localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(arr));
  } catch (err) {
    console.warn('[SDS] Failed to write to local storage.', err);
  }
}

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

// PROGRESS TRACKING & SYLLABUS ENGINE
let currentActiveTier = 'all';
let currentActiveStatus = 'all';
let currentSearchQuery = '';

function getTotalCurriculumTopicsCount() {
  if (typeof CURRICULUM_CLUSTERS === 'undefined') return 354;
  return CURRICULUM_CLUSTERS.reduce((acc, c) => acc + c.topics.length, 0);
}

function updateGlobalProgressUI(masteredSet) {
  const totalTopics = getTotalCurriculumTopicsCount();
  const completedCount = masteredSet ? masteredSet.size : getMasteredTopicIds().size;
  const percentage = totalTopics > 0 ? ((completedCount / totalTopics) * 100).toFixed(1) : '0.0';

  const badgeEl = document.getElementById('progress-percentage-badge');
  const ratioEl = document.getElementById('progress-topics-ratio');
  const fillEl = document.getElementById('curriculum-progress-fill');

  if (badgeEl) badgeEl.textContent = `${percentage}% Mastered`;
  if (ratioEl) ratioEl.textContent = `${completedCount} of ${totalTopics} topics completed`;
  if (fillEl) fillEl.style.width = `${percentage}%`;

  // Update topbar pill on any page if present
  const topbarTags = document.querySelectorAll('.version-tag');
  topbarTags.forEach(tag => {
    if (completedCount > 0) {
      tag.innerHTML = `<span class="version-dot"></span> v2.1.0 &middot; ${completedCount}/${totalTopics} mastered`;
    }
  });
}

function toggleTopicMastery(topicId, isChecked) {
  const masteredSet = getMasteredTopicIds();
  if (isChecked) {
    masteredSet.add(topicId);
  } else {
    masteredSet.delete(topicId);
  }
  saveMasteredTopicIds(masteredSet);

  // Update DOM topic row
  const safeId = topicId.replace(/[^a-zA-Z0-9_-]/g, '_');
  const rowEl = document.getElementById(`topic-row-${safeId}`);
  if (rowEl) {
    if (isChecked) {
      rowEl.classList.add('is-mastered');
    } else {
      rowEl.classList.remove('is-mastered');
    }
  }

  // Update cluster count
  if (typeof CURRICULUM_CLUSTERS !== 'undefined') {
    const parentCluster = CURRICULUM_CLUSTERS.find(c => c.topics.some(t => t.id === topicId));
    if (parentCluster) {
      const clusterCountEl = document.getElementById(`cluster-count-${parentCluster.code}`);
      if (clusterCountEl) {
        const completedInCluster = parentCluster.topics.filter(t => masteredSet.has(t.id)).length;
        clusterCountEl.textContent = `${completedInCluster}/${parentCluster.topics.length} mastered`;
      }
    }
  }

  updateGlobalProgressUI(masteredSet);

  // If filtered by status, re-filter view smoothly
  if (currentActiveStatus !== 'all') {
    renderCurriculum();
  }
}

function resetCurriculumProgress() {
  const masteredSet = getMasteredTopicIds();
  if (masteredSet.size === 0) {
    alert('No saved progress to reset.');
    return;
  }

  const confirmed = confirm(`Are you sure you want to reset all ${masteredSet.size} completed topics in browser storage?`);
  if (!confirmed) return;

  try {
    localStorage.removeItem(PROGRESS_STORAGE_KEY);
  } catch (err) {
    console.warn(err);
  }

  updateGlobalProgressUI(new Set());
  renderCurriculum();
}

function filterByStatus(statusKey, buttonEl) {
  currentActiveStatus = statusKey;
  const container = buttonEl.closest('.status-filter-pills');
  if (container) {
    container.querySelectorAll('.filter-pill').forEach(btn => btn.classList.remove('active'));
  }
  buttonEl.classList.add('active');
  renderCurriculum();
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

function renderCurriculum() {
  const displayEl = document.getElementById('clusters-display');
  const countLabel = document.getElementById('results-count-label');
  if (!displayEl || typeof CURRICULUM_CLUSTERS === 'undefined') return;

  const query = currentSearchQuery.toLowerCase().trim();
  const masteredSet = getMasteredTopicIds();

  // Filter clusters & topics
  const processedClusters = [];

  CURRICULUM_CLUSTERS.forEach(cluster => {
    // 1. Tier filter (code like "0.1", "1.4", "2.3")
    const tierMatch = currentActiveTier === 'all' || cluster.code.startsWith(currentActiveTier + '.');
    if (!tierMatch) return;

    // 2. Filter topics by search & status
    const matchingTopics = cluster.topics.filter(topic => {
      const isMastered = masteredSet.has(topic.id);

      // Status filter
      if (currentActiveStatus === 'mastered' && !isMastered) return false;
      if (currentActiveStatus === 'remaining' && isMastered) return false;

      // Query filter
      if (!query) return true;
      const inTitle = topic.title.toLowerCase().includes(query);
      const inId = topic.id.toLowerCase().includes(query);
      const inClusterTitle = cluster.title.toLowerCase().includes(query);
      const inCode = cluster.code.toLowerCase().includes(query);

      return inTitle || inId || inClusterTitle || inCode;
    });

    if (matchingTopics.length > 0) {
      processedClusters.push({
        cluster,
        visibleTopics: matchingTopics,
        completedInCluster: cluster.topics.filter(t => masteredSet.has(t.id)).length
      });
    }
  });

  const totalVisibleTopics = processedClusters.reduce((acc, c) => acc + c.visibleTopics.length, 0);

  if (countLabel) {
    countLabel.textContent = `Showing ${processedClusters.length} of ${CURRICULUM_CLUSTERS.length} clusters (${totalVisibleTopics} topics matching view)`;
  }

  if (processedClusters.length === 0) {
    displayEl.innerHTML = `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-wire); border-radius: var(--radius-md); padding: 36px; text-align: center;">
        <p style="font-size: 15px; color: var(--text-primary); margin-bottom: 8px;">No matching topics found.</p>
        <p style="font-size: 13px; color: var(--text-secondary);">Try clearing your search query or switching the status/tier filter.</p>
      </div>
    `;
    return;
  }

  displayEl.innerHTML = processedClusters.map(({ cluster, visibleTopics, completedInCluster }) => {
    const topicsHtml = visibleTopics.map(topic => {
      const isMastered = masteredSet.has(topic.id);
      const safeId = topic.id.replace(/[^a-zA-Z0-9_-]/g, '_');

      return `
        <div class="topic-row ${isMastered ? 'is-mastered' : ''}" id="topic-row-${safeId}">
          <label class="topic-check-label" title="${isMastered ? 'Mark as incomplete' : 'Mark as mastered'}">
            <input type="checkbox" class="topic-checkbox" ${isMastered ? 'checked' : ''} onchange="toggleTopicMastery('${topic.id}', this.checked)">
            <span class="topic-checkmark"></span>
          </label>
          <span class="topic-id-tag">${topic.id.replace('topic.', '')}</span>
          <span class="topic-name">${topic.title}</span>
        </div>
      `;
    }).join('');

    return `
      <article class="cluster-block" id="cluster-${cluster.code}">
        <div class="cluster-block-header">
          <div class="cluster-title-wrap">
            <span class="cluster-code-badge">${cluster.code}</span>
            <h2 class="cluster-title-text">${cluster.title.replace(/^([0-9]+\.\s*\[[0-9.]+\]\s*)/, '')}</h2>
          </div>
          <span class="cluster-topic-count" id="cluster-count-${cluster.code}">${completedInCluster}/${cluster.topics.length} mastered</span>
        </div>
        <div class="topics-grid">
          ${topicsHtml}
        </div>
      </article>
    `;
  }).join('');
}

// INITIALIZATION ON DOM READY
document.addEventListener('DOMContentLoaded', () => {
  const masteredSet = getMasteredTopicIds();

  // Update topbar tag on all pages
  updateGlobalProgressUI(masteredSet);

  // Curriculum-specific setup
  if (document.getElementById('clusters-display')) {
    const params = new URLSearchParams(window.location.search);
    const tierParam = params.get('tier');
    if (tierParam && ['0', '1', '2', '3', '4', '5'].includes(tierParam)) {
      currentActiveTier = tierParam;
      const targetBtn = document.querySelector(`.filter-pill[data-tier="${tierParam}"]`);
      if (targetBtn) {
        document.querySelectorAll('.filter-pill[data-tier]').forEach(btn => btn.classList.remove('active'));
        targetBtn.classList.add('active');
      }
    }
    renderCurriculum();
  }
});
