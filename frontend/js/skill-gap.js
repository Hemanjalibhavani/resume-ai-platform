const box = document.getElementById('result');
(async () => {
  if (needResume(box)) return;
  const mid = state.get('matchId');
  if (!mid) { box.innerHTML = '<div class="card-x"><h3>No analysis yet</h3><p class="muted">Run a job match first to see your skill gap.</p><a class="btn-grad" href="job-matching.html">Go to Job Matching</a></div>'; return; }
  try {
    const g = await api('/api/skills/gap/' + mid);
    const entries = Object.entries(g.skill_strength);
    box.innerHTML = `<div class="card-x"><h3>${esc(g.job_title)} — skill coverage</h3><div class="chart-box tall"><canvas id="gap-chart"></canvas></div>
      <p class="muted small">Matched skills score 70–100% (more evidence = higher), partial = 50%, missing = 0%.</p></div>
     <div class="grid g2"><div class="card-x"><h3>Your skills</h3>${g.your_skills.map(s => badge(s)).join('')}</div>
      <div class="card-x"><h3>Required skills</h3>${g.required_skills.map(s => badge(s)).join('')}<h4>Preferred</h4>${g.preferred_skills.map(s => badge(s)).join('') || '<span class="muted small">none</span>'}</div></div>
     <div class="card-x"><h4>✓ Matched</h4>${g.matched.map(s => badge(s, 'badge-ok')).join('') || '—'}<h4>~ Partially matched</h4>${g.partial.map(p => `<span title="${esc(p.reason)}">${badge(p.display, 'badge-part')}</span>`).join('') || '—'}<h4>✗ Missing</h4>${g.missing.map(s => badge(s, 'badge-miss')).join('') || '—'}</div>
     <h3>What to learn</h3>${g.gaps.map(x => `<div class="card-x gap-card ${x.priority}"><div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap"><h3>${esc(x.display)} ${badge(x.status, x.status === 'missing' ? 'badge-miss' : 'badge-part')}</h3>${badge('Priority: ' + x.priority, 'badge-' + x.priority.toLowerCase())}</div>
       ${x.note ? `<p class="muted small">${esc(x.note)}</p>` : ''}<p><b>Why it matters:</b> ${esc(x.why)}</p><b>Learn:</b><ol>${x.learn.map(l => `<li>${esc(l)}</li>`).join('')}</ol><p><b>Suggested project:</b> ${esc(x.project)}</p></div>`).join('') || '<div class="card-x">No gaps found. Great match!</div>'}`;
    hbar('gap-chart', entries.map(e => e[0]), entries.map(e => e[1]), entries.map(e => (e[1] >= 70 ? '#16a34a' : e[1] > 0 ? '#d97706' : '#dc2626')));
  } catch (e) { toast(e.message, 'error'); state.del('matchId'); }
})();
