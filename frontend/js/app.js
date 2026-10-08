/* Shared app shell: API client, state, toasts, loading steps, layout. */
const API_BASE = location.protocol === 'file:' ? 'http://localhost:8000' : '';
const NAV = [
  ['dashboard.html', 'fa-gauge', 'Dashboard'], ['resume.html', 'fa-file-lines', 'Resume Analyzer'],
  ['job-matching.html', 'fa-bullseye', 'Job Matching'], ['skill-gap.html', 'fa-chart-simple', 'Skill Gap Analysis'],
  ['assistant.html', 'fa-robot', 'AI Career Assistant'], ['interview.html', 'fa-user-tie', 'Interview Preparation'],
  ['resume.html#list', 'fa-folder-open', 'My Resumes'], ['history.html', 'fa-clock-rotate-left', 'Analysis History'],
  ['#settings', 'fa-gear', 'Settings'],
];
const SPECIAL = { aws: 'AWS', gcp: 'GCP', nlp: 'NLP', llm: 'LLM', rag: 'RAG', sql: 'SQL', html: 'HTML', css: 'CSS', oop: 'OOP', etl: 'ETL',
  'ci/cd': 'CI/CD', mlops: 'MLOps', fastapi: 'FastAPI', mysql: 'MySQL', postgresql: 'PostgreSQL', mongodb: 'MongoDB', sqlite: 'SQLite',
  xgboost: 'XGBoost', opencv: 'OpenCV', faiss: 'FAISS', chromadb: 'ChromaDB', github: 'GitHub', javascript: 'JavaScript',
  typescript: 'TypeScript', pytorch: 'PyTorch', tensorflow: 'TensorFlow', 'rest api': 'REST API', 'node.js': 'Node.js',
  langchain: 'LangChain', sqlalchemy: 'SQLAlchemy', 'power bi': 'Power BI', 'scikit-learn': 'scikit-learn', php: 'PHP', 'c++': 'C++', 'c#': 'C#', go: 'Go', r: 'R' };

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pretty = s => SPECIAL[s] || (s && s.includes(' ') ? s.replace(/\b\w/g, c => c.toUpperCase()) : s ? s[0].toUpperCase() + s.slice(1) : s);
const state = { get: k => localStorage.getItem(k), set: (k, v) => localStorage.setItem(k, v), del: k => localStorage.removeItem(k) };
const badge = (t, cls = '') => `<span class="badge-x ${cls}">${esc(t)}</span>`;
const scoreColor = s => (s >= 80 ? '#16a34a' : s >= 65 ? '#d97706' : '#dc2626');
const ring = (score, sm = false) => `<div class="ring ${sm ? 'sm' : ''}" style="--p:${score};--c:${scoreColor(score)}"><span>${Math.round(score)}${sm ? '' : '%'}</span></div>`;
const labelClass = l => (l === 'Best Match' ? 'lbl-best' : l === 'Recommended' ? 'lbl-rec' : 'lbl-need');
const bar = (pts, max) => `<div class="bar"><div style="width:${Math.min(100, (pts / max) * 100)}%"></div></div>`;

async function api(path, opts = {}) {
  const init = { method: opts.method || 'GET', headers: {} };
  if (opts.body instanceof FormData) init.body = opts.body;
  else if (opts.body !== undefined) { init.headers['Content-Type'] = 'application/json'; init.body = JSON.stringify(opts.body); }
  let res;
  try { res = await fetch(API_BASE + path, init); }
  catch { throw new Error('Cannot reach the server. Make sure the backend is running.'); }
  let data = null;
  try { data = await res.json(); } catch { /* non-json */ }
  if (!res.ok) throw new Error((data && data.detail) || 'Request failed. Please try again.');
  return data;
}

function notify(msg) {
  const list = JSON.parse(localStorage.getItem('notes') || '[]');
  list.unshift({ t: new Date().toLocaleTimeString(), msg });
  localStorage.setItem('notes', JSON.stringify(list.slice(0, 8)));
  document.querySelector('#bell .dot')?.classList.remove('hidden');
}
function toast(msg, type = 'info') {
  let box = document.getElementById('toasts');
  if (!box) { box = document.createElement('div'); box.id = 'toasts'; document.body.appendChild(box); }
  const el = document.createElement('div');
  el.className = `toast-x ${type}`; el.textContent = msg; box.appendChild(el);
  if (type !== 'error') notify(msg);
  setTimeout(() => el.remove(), 4000);
}

/** Show rotating progress steps while an async task runs. */
async function runSteps(steps, work) {
  const ov = document.createElement('div');
  ov.className = 'overlay';
  ov.innerHTML = `<div class="box"><div class="spinner"></div><ul class="clean steps">${steps.map((s, i) => `<li data-i="${i}"><i class="fa-regular fa-circle"></i>${esc(s)}</li>`).join('')}</ul></div>`;
  document.body.appendChild(ov);
  let i = 0;
  const tick = () => {
    ov.querySelectorAll('li').forEach((li, n) => {
      li.className = n < i ? 'done' : n === i ? 'on' : '';
      li.querySelector('i').className = n < i ? 'fa-solid fa-circle-check' : n === i ? 'fa-solid fa-circle-notch fa-spin' : 'fa-regular fa-circle';
    });
    if (i < steps.length - 1) i++;
  };
  tick();
  const timer = setInterval(tick, 650);
  try { return await work(); } finally { clearInterval(timer); ov.remove(); }
}

function needResume(target) {
  if (state.get('resumeId')) return false;
  target.innerHTML = `<div class="card-x"><h3>No resume yet</h3><p class="muted">Please upload a resume before running job matching.</p>
    <a class="btn-grad" href="resume.html"><i class="fa-solid fa-upload"></i> Upload resume</a>
    <button class="btn-soft" onclick="tryDemo()"><i class="fa-solid fa-wand-magic-sparkles"></i> Try Demo</button></div>`;
  return true;
}

/** One-click demo: sample resume + Software Developer sample JD + match, then open results. */
async function tryDemo() {
  try {
    await runSteps(['Analyzing resume...', 'Extracting skills...', 'Analyzing job description...', 'Calculating semantic similarity...', 'Finding skill gaps...', 'Generating recommendations...'], async () => {
      const r = await api('/api/resume/demo', { method: 'POST' });
      const j = await api('/api/job/samples/1', { method: 'POST' });
      const m = await api('/api/match', { method: 'POST', body: { resume_id: r.id, job_id: j.id } });
      state.set('resumeId', r.id); state.set('jobId', j.id); state.set('matchId', m.id);
    });
    location.href = 'job-matching.html';
  } catch (e) { toast(e.message, 'error'); }
}

function openModal(id) { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

async function showSettings() {
  let h = {};
  try { h = await api('/api/health'); } catch { /* offline */ }
  const m = document.getElementById('settings-body');
  m.innerHTML = `<p><b>AI mode:</b> ${esc(h.ai_mode || 'unknown')} ${h.llm_provider && h.llm_provider !== 'none' ? '(' + esc(h.llm_provider) + ')' : ''}</p>
   <p><b>Embedding backend:</b> ${esc(h.embedding_backend || 'unknown')}</p>
   <p class="muted small">API keys are read from server environment variables (.env) and are never exposed to the browser. Without a key the app runs in local analysis mode.</p>
   <button class="btn-line" onclick="if(confirm('Clear saved resume/job selection in this browser?')){['resumeId','jobId','matchId'].forEach(state.del);location.reload()}">Reset current selection</button>`;
  openModal('settings-modal');
}

function buildShell() {
  const page = document.getElementById('page');
  if (!page || document.body.dataset.shell === 'false') return;
  const file = location.pathname.split('/').pop() || 'index.html';
  const links = NAV.map(([href, icon, label]) => {
    const active = href.includes('#list') ? (file === 'resume.html' && location.hash === '#list') : (href === file && !(file === 'resume.html' && location.hash === '#list'));
    const attrs = href === '#settings' ? 'href="#" onclick="showSettings();return false"' : `href="${href}"`;
    return `<a class="nav-link-x ${active ? 'active' : ''}" ${attrs}><i class="fa-solid ${icon}"></i>${label}</a>`;
  }).join('');
  const notes = JSON.parse(localStorage.getItem('notes') || '[]');
  const wrap = document.createElement('div');
  wrap.className = 'app-shell';
  wrap.innerHTML = `<aside class="sidebar" id="sidebar"><a class="brand" href="index.html"><i class="fa-solid fa-brain"></i>ResumeAI</a>${links}</aside>
  <div class="main-col"><header class="topbar">
    <button class="icon-btn menu-toggle" onclick="document.getElementById('sidebar').classList.toggle('open')" aria-label="Menu"><i class="fa-solid fa-bars"></i></button>
    <form class="search" onsubmit="event.preventDefault();location.href='assistant.html?q='+encodeURIComponent(this.q.value)"><i class="fa-solid fa-magnifying-glass"></i><input name="q" placeholder="Ask the AI assistant..." autocomplete="off"></form>
    <span style="flex:1"></span><span class="mode-pill" id="mode-pill">checking...</span>
    <button class="icon-btn" id="bell" aria-label="Notifications"><i class="fa-regular fa-bell"></i><span class="dot ${notes.length ? '' : 'hidden'}"></span></button>
    <div class="avatar" title="Demo User">DU</div></header>
    <div class="dropdown-x" id="notes"></div><div class="content" id="content"></div></div>
  <div class="modal-x" id="settings-modal"><div class="box"><div style="display:flex;justify-content:space-between"><h3>Settings</h3><button class="icon-btn" onclick="closeModal('settings-modal')"><i class="fa-solid fa-xmark"></i></button></div><div id="settings-body"></div></div></div>`;
  document.body.prepend(wrap);
  wrap.querySelector('#content').appendChild(page);
  document.getElementById('bell').onclick = () => {
    const n = JSON.parse(localStorage.getItem('notes') || '[]');
    const d = document.getElementById('notes');
    d.innerHTML = '<b>Notifications</b>' + (n.length ? n.map(x => `<div class="small" style="padding:.4rem 0;border-bottom:1px solid var(--line)"><span class="muted">${x.t}</span> ${esc(x.msg)}</div>`).join('') : '<p class="muted small">Nothing new.</p>');
    d.classList.toggle('show'); document.querySelector('#bell .dot').classList.add('hidden');
  };
  api('/api/health').then(h => {
    const p = document.getElementById('mode-pill');
    p.textContent = h.ai_mode === 'llm' ? `AI: ${h.llm_provider}` : 'Local analysis mode';
    p.className = 'mode-pill ' + (h.ai_mode === 'llm' ? 'llm' : '');
    p.title = h.message || 'LLM connected';
  }).catch(() => { document.getElementById('mode-pill').textContent = 'Backend offline'; });
}
document.addEventListener('DOMContentLoaded', buildShell);
