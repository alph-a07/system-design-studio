/*
  System Design Studio — Interactive Application Engine
  Counts and tier metadata are derived from curriculum-data.js.
  Persistent progress stored in browser local storage.
*/

// STORAGE KEY FOR COMPLETED TOPICS (with fallback for legacy key)
const PROGRESS_STORAGE_KEY = 'sds_completed_topics';
const LEGACY_STORAGE_KEY = 'sds_mastered_topics';

function getCompletedTopicIds() {
  try {
    let raw = localStorage.getItem(PROGRESS_STORAGE_KEY);
    if (!raw) {
      raw = localStorage.getItem(LEGACY_STORAGE_KEY);
    }
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? new Set(parsed) : new Set();
  } catch (err) {
    console.warn('[SDS] Local storage not accessible; using memory.', err);
    return new Set();
  }
}

function saveCompletedTopicIds(topicSet) {
  try {
    const arr = Array.from(topicSet);
    localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(arr));
  } catch (err) {
    console.warn('[SDS] Failed to write to local storage.', err);
  }
}

// Backward-compatibility aliases
const getMasteredTopicIds = getCompletedTopicIds;
const saveMasteredTopicIds = saveCompletedTopicIds;

// INSTALLATION METHOD CONFIGURATION
const INSTALL_COMMANDS = {
  quickstart: {
    command: `# Universal 1-line installer: detects agents and installs verified skill\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash`,
    target: 'Target: Universal Installer (Antigravity, Claude, Cursor, Codex)',
    orderNote: 'Installs verified skill to global agent discovery paths and auto-scaffolds .system-design/ on first chat prompt.',
    viewScriptUrl: 'https://github.com/alph-a07/system-design-studio/blob/main/install.sh'
  },
  agy: {
    command: `# Install skill into Google Antigravity\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --antigravity`,
    target: 'Target: Google Antigravity (~/.gemini/antigravity/skills/ & ~/.gemini/config/skills/)',
    orderNote: 'Places skill in Antigravity global paths; auto-scaffolds .system-design/ on first chat prompt.',
    viewScriptUrl: 'https://github.com/alph-a07/system-design-studio/blob/main/install.sh'
  },
  claude: {
    command: `# Install skill to Claude Code skills directory\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --claude`,
    target: 'Target: Anthropic Claude Code (~/.claude/skills/system-design-studio)',
    orderNote: 'Places skill into ~/.claude/skills/; ready to use in any Claude Code chat.',
    viewScriptUrl: 'https://github.com/alph-a07/system-design-studio/blob/main/install.sh'
  },
  cursor: {
    command: `# Step 1: Install skill into Cursor IDE skills directory\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --cursor\n\n# Step 2: Append project rules into your active workspace\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/templates/.cursorrules >> .cursorrules`,
    target: 'Target: Cursor IDE (~/.cursor/skills/ & .cursorrules)',
    orderNote: 'Places skill into ~/.cursor/skills/ and configures project .cursorrules.',
    viewScriptUrl: 'https://github.com/alph-a07/system-design-studio/blob/main/templates/.cursorrules'
  },
  codex: {
    command: `# Install skill into OpenAI Codex directory\ncurl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/install.sh | bash -s -- --codex`,
    target: 'Target: OpenAI Codex (~/.codex/skills/system-design-studio)',
    orderNote: 'Places skill into ~/.codex/skills/; ready to use in any Codex chat.',
    viewScriptUrl: 'https://github.com/alph-a07/system-design-studio/blob/main/install.sh'
  }
};

function switchInstallTab(method, buttonEl) {
  const cfg = INSTALL_COMMANDS[method];
  if (!cfg) return;

  const codeEl = document.getElementById('install-command-text');
  const targetEl = document.getElementById('install-target-label');
  const orderNoteEl = document.getElementById('install-order-note');
  const scriptLinkEl = document.getElementById('install-view-script-link');

  if (codeEl) codeEl.textContent = cfg.command;
  if (targetEl) targetEl.textContent = cfg.target;
  if (orderNoteEl) orderNoteEl.textContent = cfg.orderNote;

  if (scriptLinkEl) {
    if (cfg.viewScriptUrl) {
      scriptLinkEl.href = cfg.viewScriptUrl;
      scriptLinkEl.style.display = 'inline-flex';
    } else {
      scriptLinkEl.style.display = 'none';
    }
  }

  const container = buttonEl.closest('.install-tabs');
  if (container) {
    container.querySelectorAll('.install-tab').forEach(btn => btn.classList.remove('active'));
  }
  buttonEl.classList.add('active');
}

// CLIPBOARD COPY HELPER
function copySnippet(buttonEl, sourceId) {
  const sourceEl = document.getElementById(sourceId);
  if (!sourceEl) return;

  const textToCopy = sourceEl.textContent.trim();
  navigator.clipboard.writeText(textToCopy).then(() => {
    const originalHtml = buttonEl.innerHTML;
    buttonEl.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
      <span style="color: #10b981;">Copied</span>
    `;
    setTimeout(() => {
      buttonEl.innerHTML = originalHtml;
    }, 2000);
  }).catch(() => {
    const input = document.createElement('textarea');
    input.value = textToCopy;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    document.body.removeChild(input);
  });
}

// HERO CONSOLE TAB SWITCHER (CURSOR.md vs sync-status.py)
function switchConsoleTab(tabKey, buttonEl) {
  const viewCursor = document.getElementById('console-view-cursor');
  const viewTerminal = document.getElementById('console-view-terminal');

  if (viewCursor) viewCursor.style.display = tabKey === 'cursor' ? 'block' : 'none';
  if (viewTerminal) viewTerminal.style.display = tabKey === 'terminal' ? 'block' : 'none';

  const container = buttonEl.closest('.console-nav-tabs');
  if (container) {
    container.querySelectorAll('.console-tab').forEach(tab => tab.classList.remove('active'));
  }
  buttonEl.classList.add('active');
}

// INTERACTIVE PROTOCOL SIMULATOR STATE & LOGIC
let simState = {
  protocol: 'tcp', // 'tcp' or 'quic'
  packet2Dropped: true
};

function setSimulatorProtocol(proto) {
  simState.protocol = proto;
  const btnTcp = document.getElementById('sim-btn-tcp');
  const btnQuic = document.getElementById('sim-btn-quic');

  if (btnTcp) {
    btnTcp.classList.toggle('active', proto === 'tcp');
    btnTcp.setAttribute('aria-selected', proto === 'tcp' ? 'true' : 'false');
  }
  if (btnQuic) {
    btnQuic.classList.toggle('active', proto === 'quic');
    btnQuic.setAttribute('aria-selected', proto === 'quic' ? 'true' : 'false');
  }

  renderSimulatorUI();
}

function togglePacket2Drop() {
  simState.packet2Dropped = !simState.packet2Dropped;
  renderSimulatorUI();
}

function renderSimulatorUI() {
  const pkt1El = document.getElementById('sim-pkt-1');
  const pkt2El = document.getElementById('sim-pkt-2');
  const pkt3El = document.getElementById('sim-pkt-3');
  const pkt4El = document.getElementById('sim-pkt-4');
  const actionBtn = document.getElementById('sim-action-btn');
  const statusBadge = document.getElementById('sim-status-badge');
  const explainText = document.getElementById('sim-explain-text');
  const penaltyPill = document.getElementById('sim-penalty-pill');

  if (!pkt2El) return;

  const isTcp = simState.protocol === 'tcp';
  const dropped = simState.packet2Dropped;

  if (pkt1El) {
    pkt1El.setAttribute('aria-label', 'Packet 1: Acknowledged');
  }

  if (actionBtn) {
    const actionLabel = dropped ? 'Retransmit Packet 2' : 'Inject Packet 2 Drop';
    actionBtn.textContent = actionLabel;
    actionBtn.setAttribute('aria-label', dropped ? 'Retransmit Packet 2 to unblock socket stream' : 'Simulate Packet 2 network drop');
  }

  if (dropped) {
    pkt2El.className = 'sim-packet-box status-lost';
    pkt2El.setAttribute('aria-label', 'Packet 2: Lost in transit');
    const pkt2Tag = pkt2El.querySelector('.sim-packet-tag');
    if (pkt2Tag) {
      pkt2Tag.textContent = 'LOST';
      pkt2Tag.style.color = '#ef4444';
    }

    if (isTcp) {
      // TCP HOL Blocking: Packets 3 & 4 blocked in socket buffer
      if (pkt3El) {
        pkt3El.className = 'sim-packet-box status-blocked';
        pkt3El.setAttribute('aria-label', 'Packet 3: Blocked by socket buffer');
        const tag = pkt3El.querySelector('.sim-packet-tag');
        if (tag) { tag.textContent = 'BLOCKED'; tag.style.color = 'var(--text-muted)'; }
      }

      if (pkt4El) {
        pkt4El.className = 'sim-packet-box status-blocked';
        pkt4El.setAttribute('aria-label', 'Packet 4: Blocked by socket buffer');
        const tag = pkt4El.querySelector('.sim-packet-tag');
        if (tag) { tag.textContent = 'BLOCKED'; tag.style.color = 'var(--text-muted)'; }
      }

      if (statusBadge) {
        statusBadge.textContent = 'HOL BLOCKING ACTIVE';
        statusBadge.style.color = '#ef4444';
        statusBadge.style.background = 'rgba(239, 68, 68, 0.1)';
      }
      if (explainText) {
        explainText.textContent = 'Single-stream TCP socket buffer stall: Packets 3 and 4 cannot be consumed by the application layer until Packet 2 is retransmitted and acknowledged.';
      }
      if (penaltyPill) {
        penaltyPill.innerHTML = '<span style="color: #ef4444;">Transport Stall: +84ms RTT penalty</span>';
      }
    } else {
      // QUIC / HTTP/3: Independent streams continue without HOL blocking
      if (pkt3El) {
        pkt3El.className = 'sim-packet-box status-acked';
        pkt3El.setAttribute('aria-label', 'Stream 3: Delivered over UDP frame');
        const tag = pkt3El.querySelector('.sim-packet-tag');
        if (tag) { tag.textContent = 'DELIVERED'; tag.style.color = 'var(--accent-diode)'; }
      }

      if (pkt4El) {
        pkt4El.className = 'sim-packet-box status-acked';
        pkt4El.setAttribute('aria-label', 'Stream 4: Delivered over UDP frame');
        const tag = pkt4El.querySelector('.sim-packet-tag');
        if (tag) { tag.textContent = 'DELIVERED'; tag.style.color = 'var(--accent-diode)'; }
      }

      if (statusBadge) {
        statusBadge.textContent = 'NO HOL BLOCKING';
        statusBadge.style.color = 'var(--accent-diode)';
        statusBadge.style.background = 'var(--accent-diode-surface)';
      }
      if (explainText) {
        explainText.textContent = 'QUIC multiplexed independent streams: Streams 3 and 4 deliver immediately over UDP framing. Only Stream 2 waits for retransmission.';
      }
      if (penaltyPill) {
        penaltyPill.innerHTML = '<span style="color: var(--accent-diode);">Stream Isolation: 0ms stall on streams 3/4</span>';
      }
    }
  } else {
    // Healthy stream: all ACKed
    pkt2El.className = 'sim-packet-box status-acked';
    pkt2El.setAttribute('aria-label', 'Packet 2: Acknowledged');
    const pkt2Tag = pkt2El.querySelector('.sim-packet-tag');
    if (pkt2Tag) {
      pkt2Tag.textContent = 'ACK';
      pkt2Tag.style.color = 'var(--accent-diode)';
    }

    if (pkt3El) {
      pkt3El.className = 'sim-packet-box status-acked';
      pkt3El.setAttribute('aria-label', 'Packet 3: Acknowledged');
      const tag = pkt3El.querySelector('.sim-packet-tag');
      if (tag) { tag.textContent = 'ACK'; tag.style.color = 'var(--accent-diode)'; }
    }

    if (pkt4El) {
      pkt4El.className = 'sim-packet-box status-acked';
      pkt4El.setAttribute('aria-label', 'Packet 4: Acknowledged');
      const tag = pkt4El.querySelector('.sim-packet-tag');
      if (tag) { tag.textContent = 'ACK'; tag.style.color = 'var(--accent-diode)'; }
    }

    if (statusBadge) {
      statusBadge.textContent = 'STREAM NOMINAL';
      statusBadge.style.color = 'var(--accent-diode)';
      statusBadge.style.background = 'var(--accent-diode-surface)';
    }
    if (explainText) {
      explainText.textContent = 'All packets acknowledged sequentially. Socket receive buffer reading in continuous byte-stream order.';
    }
    if (penaltyPill) {
      penaltyPill.innerHTML = '<span style="color: var(--text-secondary);">Latency: 84ms nominal WAN RTT</span>';
    }
  }
}

// PROGRESS TRACKING & SYLLABUS ENGINE
let currentActiveTier = 'all';
let currentActiveStatus = 'all';
let currentSearchQuery = '';

function getTotalCurriculumTopicsCount() {
  if (typeof getCurriculumStats === 'function') {
    return getCurriculumStats().totalTopics;
  }
  if (typeof CURRICULUM_CLUSTERS !== 'undefined') {
    return CURRICULUM_CLUSTERS.reduce((acc, c) => acc + c.topics.length, 0);
  }
  return 354;
}

function updateGlobalProgressUI(completedSet) {
  const totalTopics = getTotalCurriculumTopicsCount();
  const completedCount = completedSet ? completedSet.size : getCompletedTopicIds().size;
  const percentage = totalTopics > 0 ? ((completedCount / totalTopics) * 100).toFixed(1) : '0.0';

  const badgeEl = document.getElementById('progress-percentage-badge');
  const ratioEl = document.getElementById('progress-topics-ratio');
  const fillEl = document.getElementById('curriculum-progress-fill');

  if (badgeEl) badgeEl.textContent = `${percentage}% Complete`;
  if (ratioEl) ratioEl.textContent = `${completedCount} of ${totalTopics} topics completed`;
  if (fillEl) fillEl.style.width = `${percentage}%`;

  const topbarTags = document.querySelectorAll('.version-tag');
  topbarTags.forEach(tag => {
    if (completedCount > 0) {
      tag.innerHTML = `<span class="version-dot"></span> v3.0.0 · ${completedCount}/${totalTopics} completed`;
    } else {
      tag.innerHTML = `<span class="version-dot"></span> v3.0.0 · ${totalTopics} topics`;
    }
  });
}

function toggleTopicCompletion(topicId, isChecked) {
  const completedSet = getCompletedTopicIds();
  if (isChecked) {
    completedSet.add(topicId);
  } else {
    completedSet.delete(topicId);
  }
  saveCompletedTopicIds(completedSet);

  const safeId = topicId.replace(/[^a-zA-Z0-9_-]/g, '_');
  const rowEl = document.getElementById(`topic-row-${safeId}`);
  if (rowEl) {
    if (isChecked) {
      rowEl.classList.add('is-completed', 'is-mastered');
    } else {
      rowEl.classList.remove('is-completed', 'is-mastered');
    }
  }

  if (typeof CURRICULUM_CLUSTERS !== 'undefined') {
    const parentCluster = CURRICULUM_CLUSTERS.find(c => c.topics.some(t => t.id === topicId));
    if (parentCluster) {
      const clusterCountEl = document.getElementById(`cluster-count-${parentCluster.code}`);
      if (clusterCountEl) {
        const completedInCluster = parentCluster.topics.filter(t => completedSet.has(t.id)).length;
        clusterCountEl.textContent = `${completedInCluster}/${parentCluster.topics.length} completed`;
      }
    }
  }

  updateGlobalProgressUI(completedSet);

  if (currentActiveStatus !== 'all') {
    renderCurriculum();
  }
}



function resetCurriculumProgress() {
  const completedSet = getCompletedTopicIds();
  if (completedSet.size === 0) {
    alert('No saved progress to reset.');
    return;
  }

  const confirmed = confirm(`Reset all ${completedSet.size} completed topics in browser storage?`);
  if (!confirmed) return;

  try {
    localStorage.removeItem(PROGRESS_STORAGE_KEY);
    localStorage.removeItem(LEGACY_STORAGE_KEY);
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
  const completedSet = getCompletedTopicIds();

  const processedClusters = [];

  CURRICULUM_CLUSTERS.forEach(cluster => {
    const tierMatch = currentActiveTier === 'all' || cluster.code.startsWith(currentActiveTier + '.');
    if (!tierMatch) return;

    const matchingTopics = cluster.topics.filter(topic => {
      const isCompleted = completedSet.has(topic.id);

      if (currentActiveStatus === 'completed' && !isCompleted) return false;
      if (currentActiveStatus === 'mastered' && !isCompleted) return false;
      if (currentActiveStatus === 'remaining' && isCompleted) return false;

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
        completedInCluster: cluster.topics.filter(t => completedSet.has(t.id)).length
      });
    }
  });

  const totalVisibleTopics = processedClusters.reduce((acc, c) => acc + c.visibleTopics.length, 0);

  if (countLabel) {
    countLabel.textContent = `Showing ${processedClusters.length} of ${CURRICULUM_CLUSTERS.length} clusters (${totalVisibleTopics} topics matching view)`;
  }

  if (processedClusters.length === 0) {
    displayEl.innerHTML = `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-wire); border-radius: var(--radius-md); padding: 32px 20px; text-align: center;">
        <p style="font-size: 14.5px; color: var(--text-primary); margin-bottom: 6px;">No matching topics found.</p>
        <p style="font-size: 13px; color: var(--text-secondary);">Try clearing your search query or switching tier filters.</p>
      </div>
    `;
    return;
  }

  displayEl.innerHTML = processedClusters.map(({ cluster, visibleTopics, completedInCluster }) => {
    const topicsHtml = visibleTopics.map(topic => {
      const isCompleted = completedSet.has(topic.id);
      const safeId = topic.id.replace(/[^a-zA-Z0-9_-]/g, '_');

      return `
        <div class="topic-row ${isCompleted ? 'is-completed is-mastered' : ''}" id="topic-row-${safeId}">
          <label class="topic-check-label" title="${isCompleted ? 'Mark as incomplete' : 'Mark as completed'}">
            <input type="checkbox" class="topic-checkbox" ${isCompleted ? 'checked' : ''} onchange="toggleTopicCompletion('${topic.id}', this.checked)">
            <span class="topic-checkmark"></span>
          </label>
          <div class="topic-info-col">
            <span class="topic-name">${topic.title}</span>
            <span class="topic-id-tag">${topic.id.replace('topic.', '')}</span>
          </div>
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
          <span class="cluster-topic-count" id="cluster-count-${cluster.code}">${completedInCluster}/${cluster.topics.length} completed</span>
        </div>
        <div class="topics-grid">
          ${topicsHtml}
        </div>
      </article>
    `;
  }).join('');
}

// BIND DATA ATTRIBUTES FROM CANONICAL DATASET
function syncCurriculumCounts() {
  if (typeof getCurriculumStats !== 'function') return;
  const stats = getCurriculumStats();

  document.querySelectorAll('[data-stat="total-topics"]').forEach(el => {
    el.textContent = stats.totalTopics;
  });

  document.querySelectorAll('[data-stat="total-clusters"]').forEach(el => {
    el.textContent = stats.totalClusters;
  });

  ['0', '1', '2', '3', '4'].forEach(tierKey => {
    const tierData = stats.tiers[tierKey];
    if (!tierData) return;

    document.querySelectorAll(`[data-stat="tier-cluster-count"][data-tier="${tierKey}"]`).forEach(el => {
      el.textContent = tierData.clusterCount;
    });

    document.querySelectorAll(`[data-stat="tier-topic-count"][data-tier="${tierKey}"]`).forEach(el => {
      el.textContent = tierData.topicCount;
    });

    document.querySelectorAll(`[data-stat="tier-name"][data-tier="${tierKey}"]`).forEach(el => {
      el.textContent = tierData.meta.name;
    });

    document.querySelectorAll(`[data-stat="tier-title"][data-tier="${tierKey}"]`).forEach(el => {
      el.textContent = tierData.meta.title;
    });
  });
}

// DOCS SIDEBAR SCROLL SPY
function initDocsScrollSpy() {
  const sections = document.querySelectorAll('.docs-section');
  const links = document.querySelectorAll('.docs-sidebar-link');
  if (sections.length === 0 || links.length === 0) return;

  function onScroll() {
    let currentId = '';
    const scrollPos = window.scrollY + 120;

    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = section.getAttribute('id');
      }
    });

    if (currentId) {
      links.forEach(link => {
        const href = link.getAttribute('href');
        if (href === `#${currentId}`) {
          link.classList.add('active');
        } else {
          link.classList.remove('active');
        }
      });
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

// INITIALIZATION
document.addEventListener('DOMContentLoaded', () => {
  // Sync all counts from canonical dataset
  syncCurriculumCounts();

  const completedSet = getCompletedTopicIds();
  updateGlobalProgressUI(completedSet);

  // Initialize interactive simulator if present
  renderSimulatorUI();

  // Keyboard accessibility for action button in simulator
  const simActionBtn = document.getElementById('sim-action-btn');
  if (simActionBtn) {
    simActionBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        togglePacket2Drop();
      }
    });
  }

  // Initialize docs scroll spy if on docs page
  initDocsScrollSpy();

  // Curriculum page filter setup
  if (document.getElementById('clusters-display')) {
    const params = new URLSearchParams(window.location.search);
    const tierParam = params.get('tier');
    if (tierParam && ['0', '1', '2', '3', '4'].includes(tierParam)) {
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
