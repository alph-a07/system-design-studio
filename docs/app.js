// System Design Studio — Product Scripts (Unslopped)

function copyText(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = btn.textContent;
    btn.textContent = "Copied";
    btn.style.color = "#10b981";
    setTimeout(() => {
      btn.textContent = originalText;
      btn.style.color = "";
    }, 1500);
  });
}

function switchTab(tabId) {
  const allBtns = document.querySelectorAll('.tab-btn');
  const allContents = document.querySelectorAll('.tab-content');

  allBtns.forEach(b => b.classList.remove('active'));
  allContents.forEach(c => c.classList.remove('active'));

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  const activeContent = document.getElementById(tabId);

  if (activeBtn) activeBtn.classList.add('active');
  if (activeContent) activeContent.classList.add('active');
}

function switchInstallMethod(method) {
  const installCode = document.getElementById('install-command-code');
  const btns = document.querySelectorAll('.install-toggle-btn');

  btns.forEach(b => {
    b.style.backgroundColor = 'transparent';
    b.style.color = 'var(--text-secondary)';
    b.style.borderColor = 'transparent';
  });

  const activeBtn = document.querySelector(`.install-toggle-btn[data-method="${method}"]`);
  if (activeBtn) {
    activeBtn.style.backgroundColor = 'var(--bg-raised)';
    activeBtn.style.color = 'var(--text-primary)';
    activeBtn.style.borderColor = 'var(--border-subtle)';
  }

  if (method === 'curl') {
    installCode.textContent = 'curl -fsSL https://raw.githubusercontent.com/alph-a07/system-design-studio/main/skills/system-design-studio/scripts/init-learning-instance.sh | bash';
  } else if (method === 'agy') {
    installCode.textContent = 'agy plugin add https://github.com/alph-a07/system-design-studio.git';
  } else if (method === 'git') {
    installCode.textContent = 'git clone https://github.com/alph-a07/system-design-studio.git && skills/system-design-studio/scripts/init-learning-instance.sh';
  }
}
