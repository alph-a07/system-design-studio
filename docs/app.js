// System Design Studio — Unslopped Interactive Logic

// 1. Live Head-of-Line Blocking Simulator (TCP vs QUIC)
let simStepIndex = 0;
let packetDropped = false;

const packets = [
  { id: 1, stream: "A", name: "CSS styles.css", status: "queued" },
  { id: 2, stream: "B", name: "Image hero.png", status: "queued" },
  { id: 3, stream: "A", name: "CSS chunk #2", status: "queued" },
  { id: 4, stream: "C", name: "API /user/me", status: "queued" }
];

function renderSimulator() {
  const container = document.getElementById('sim-packet-track');
  const bufferLog = document.getElementById('sim-buffer-log');
  const dropBtn = document.getElementById('sim-drop-btn');
  const modeSelect = document.getElementById('sim-mode-select');

  if (!container) return;

  const mode = modeSelect ? modeSelect.value : 'tcp';
  container.innerHTML = '';

  packets.forEach(pkt => {
    const chip = document.createElement('div');
    chip.className = 'packet-chip';
    
    let bg = '#1a1e28';
    let border = 'rgba(238, 240, 245, 0.12)';
    let text = '#eef0f5';

    if (pkt.status === 'in-flight') {
      bg = '#222736';
      border = '#10b981';
    } else if (pkt.status === 'delivered') {
      bg = 'rgba(16, 185, 129, 0.15)';
      border = '#10b981';
      text = '#4cc38a';
    } else if (pkt.status === 'blocked') {
      bg = 'rgba(245, 158, 11, 0.15)';
      border = '#f59e0b';
      text = '#f59e0b';
    } else if (pkt.status === 'dropped') {
      bg = 'rgba(229, 72, 77, 0.15)';
      border = '#e5484d';
      text = '#e5484d';
    }

    chip.style.cssText = `
      padding: 10px 14px;
      border-radius: 8px;
      background: ${bg};
      border: 1px solid ${border};
      color: ${text};
      font-size: 12px;
      font-family: ui-monospace, monospace;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 130px;
      transition: all 0.2s ease;
    `;

    chip.innerHTML = `
      <div style="display:flex; justify-content:space-between; font-weight:600;">
        <span>Stream ${pkt.stream}</span>
        <span style="font-size:10px; opacity:0.8;">#${pkt.id}</span>
      </div>
      <div style="font-size:11px; color:#a3a9b8;">${pkt.name}</div>
      <div style="font-size:10px; text-transform:uppercase; font-weight:600; margin-top:2px;">[${pkt.status}]</div>
    `;

    container.appendChild(chip);
  });

  if (bufferLog) {
    if (simStepIndex === 0) {
      bufferLog.innerHTML = `<span style="color:#7a8296;">Status: Idle. Click <strong>Step Forward</strong> to dispatch packet sequence.</span>`;
    } else if (packetDropped && mode === 'tcp') {
      bufferLog.innerHTML = `<span style="color:#e5484d; font-weight:600;">[HOL BLOCKING]</span> Packet #2 (Stream B) was dropped! In TCP, Stream A and C are fully arrived but held hostage in OS kernel buffer until #2 retransmits!`;
    } else if (packetDropped && mode === 'quic') {
      bufferLog.innerHTML = `<span style="color:#10b981; font-weight:600;">[QUIC INDEPENDENCE]</span> Packet #2 (Stream B) was dropped, but QUIC streams are independent! Stream A (#1, #3) and Stream C (#4) deliver to the application with 0ms delay!`;
    } else if (simStepIndex >= 4) {
      bufferLog.innerHTML = `<span style="color:#10b981; font-weight:600;">[COMPLETED]</span> All frames delivered and application state updated.`;
    }
  }
}

function simStep() {
  const mode = document.getElementById('sim-mode-select')?.value || 'tcp';

  if (simStepIndex === 0) {
    packets[0].status = 'in-flight';
    simStepIndex = 1;
  } else if (simStepIndex === 1) {
    packets[0].status = 'delivered';
    packets[1].status = packetDropped ? 'dropped' : 'in-flight';
    simStepIndex = 2;
  } else if (simStepIndex === 2) {
    if (packetDropped) {
      if (mode === 'tcp') {
        packets[2].status = 'blocked';
        packets[3].status = 'blocked';
      } else {
        packets[2].status = 'delivered';
        packets[3].status = 'delivered';
      }
    } else {
      packets[1].status = 'delivered';
      packets[2].status = 'in-flight';
    }
    simStepIndex = 3;
  } else if (simStepIndex === 3) {
    if (!packetDropped) {
      packets[2].status = 'delivered';
      packets[3].status = 'delivered';
    }
    simStepIndex = 4;
  }
  renderSimulator();
}

function simToggleDrop() {
  packetDropped = !packetDropped;
  const btn = document.getElementById('sim-drop-btn');
  if (btn) {
    btn.textContent = packetDropped ? "Drop: Active (Pkt #2)" : "Inject Packet Loss";
    btn.style.borderColor = packetDropped ? "#e5484d" : "rgba(238, 240, 245, 0.08)";
    btn.style.color = packetDropped ? "#e5484d" : "#eef0f5";
  }
  simReset();
}

function simReset() {
  simStepIndex = 0;
  packets[0].status = 'queued';
  packets[1].status = 'queued';
  packets[2].status = 'queued';
  packets[3].status = 'queued';
  renderSimulator();
}

// 2. Clipboard Copier
function copyCode(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "Copied";
    setTimeout(() => { btn.textContent = original; }, 1500);
  });
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  renderSimulator();
});
