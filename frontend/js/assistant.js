const msgs = document.getElementById('msgs'), input = document.getElementById('q');
function add(role, text, sources) {
  const d = document.createElement('div');
  d.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
  d.textContent = text;
  if (sources && sources.length) {
    const s = document.createElement('details'); s.className = 'small'; s.style.marginTop = '.5rem';
    s.innerHTML = `<summary class="muted">Sources (${sources.length})</summary>` + sources.map(x => `<div class="muted">• <b>${esc(x.source)}</b>: ${esc(x.snippet)}…</div>`).join('');
    d.appendChild(s);
  }
  msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight;
}
async function ask(q) {
  q = (q || input.value).trim();
  if (!q) return;
  const rid = state.get('resumeId');
  if (!rid) return toast('Please upload a resume before running job matching.', 'error');
  input.value = ''; add('user', q);
  try {
    const r = await api('/api/assistant/chat', { method: 'POST', body: { resume_id: +rid, question: q, match_id: state.get('matchId') ? +state.get('matchId') : null } });
    add('bot', r.answer, r.sources);
  } catch (e) { add('bot', e.message); }
}
document.getElementById('send').onclick = () => ask();
input.addEventListener('keydown', e => { if (e.key === 'Enter') ask(); });
document.querySelectorAll('.chip').forEach(c => (c.onclick = () => ask(c.textContent)));
(async () => {
  const rid = state.get('resumeId');
  if (!rid) { add('bot', 'Please upload a resume (or click Try Demo) so I can answer from your documents.'); return; }
  add('bot', 'Hi! Ask me about your resume, skill gaps or match score. I answer only from your uploaded documents.');
  try { (await api('/api/assistant/history/' + rid)).slice(-8).forEach(m => add(m.role === 'user' ? 'user' : 'bot', m.message)); } catch { /* ignore */ }
  const q = new URLSearchParams(location.search).get('q');
  if (q) ask(q);
})();
