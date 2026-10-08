const res = document.getElementById('result');
function jdCard(j) {
  const list = (l, cls = '') => l && l.length ? l.map(s => badge(pretty(s), cls)).join('') : '<span class="muted small">none</span>';
  return `<div class="card-x"><h3><i class="fa-solid fa-briefcase"></i> ${esc(j.title)}</h3>
   <div class="grid g2"><div><h4>Required skills</h4>${list(j.required_skills)}<h4>Preferred skills</h4>${list(j.preferred_skills)}<h4>Soft skills</h4>${list(j.soft_skills)}</div>
   <div><h4>Languages</h4>${list(j.languages)}<h4>Frameworks</h4>${list(j.frameworks)}<h4>Tools / cloud</h4>${list(j.tools)}
   <p class="small"><b>Education:</b> ${esc(j.education_requirement)} &nbsp; <b>Experience:</b> ${j.experience_years ? j.experience_years + '+ years' : 'Entry level'}</p></div></div>
   ${j.responsibilities.length ? '<h4>Responsibilities</h4><ul class="clean">' + j.responsibilities.map(r => `<li><i class="fa-solid fa-angle-right"></i>${esc(r)}</li>`).join('') + '</ul>' : ''}</div>`;
}
function renderMatch(m, job) {
  const names = { skills: 'Technical Skills', semantic: 'Semantic Similarity', experience: 'Experience', projects: 'Projects', education: 'Education', soft_skills: 'Soft Skills' };
  res.innerHTML = `${job ? jdCard(job) : ''}
  <div class="card-x"><div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center">${ring(m.score)}
   <div style="flex:1;min-width:260px"><h3>Resume–Job Match: <span class="${labelClass(m.label)}">${esc(m.label)}</span></h3>
   <p class="muted">${esc(m.job_title)} · ${esc(m.candidate)} · similarity engine: ${esc(m.embedding_backend)}</p>
   <p class="small">${esc(m.explanation)}</p></div></div></div>
  <div class="card-x"><h3>Why this score?</h3>${Object.entries(m.breakdown).map(([k, v]) => `<div class="bar-row"><span>${names[k]}</span>${bar(v.points, v.max)}<b>${v.points}/${v.max}</b></div><div class="muted small" style="margin:-.3rem 0 .4rem">${esc(v.reason)}</div>`).join('')}</div>
  <div class="card-x"><h3>Skills</h3><h4>✓ Matched</h4>${m.matched_skills.map(s => badge(pretty(s), 'badge-ok')).join('') || '<span class="muted small">none</span>'}
   <h4>~ Partially matched</h4>${m.partial_skills.map(p => `<span title="${esc(p.reason)}">${badge(pretty(p.skill), 'badge-part')}</span>`).join('') || '<span class="muted small">none</span>'}
   <h4>✗ Missing</h4>${m.missing_skills.map(s => badge(pretty(s), 'badge-miss')).join('') || '<span class="muted small">none</span>'}</div>
  <div class="grid g2"><div class="card-x"><h3>Strengths</h3><ul class="clean good">${m.strengths.map(s => `<li><i class="fa-solid fa-check"></i>${esc(s)}</li>`).join('')}</ul></div>
   <div class="card-x"><h3>Weaknesses</h3><ul class="clean bad">${m.weaknesses.map(s => `<li><i class="fa-solid fa-triangle-exclamation"></i>${esc(s)}</li>`).join('')}</ul></div></div>
  <div class="card-x"><h3><i class="fa-solid fa-lightbulb"></i> Career recommendations</h3><ul class="clean">${m.recommendations.map(r => `<li><i class="fa-solid fa-angle-right"></i>${esc(r.text)}</li>`).join('')}</ul>
   <a class="btn-grad" href="skill-gap.html"><i class="fa-solid fa-chart-simple"></i> Skill gap analysis</a>
   <a class="btn-soft" href="assistant.html"><i class="fa-solid fa-robot"></i> Ask AI assistant</a>
   <a class="btn-soft" href="interview.html"><i class="fa-solid fa-user-tie"></i> Interview prep</a></div>`;
}

async function analyze() {
  const rid = state.get('resumeId');
  if (!rid) return toast('Please upload a resume before running job matching.', 'error');
  const text = document.getElementById('jd').value.trim(), file = document.getElementById('jdfile').files[0], sample = document.getElementById('sample').value;
  if (!text && !file && !sample) return toast('Please provide a job description.', 'error');
  try {
    const m = await runSteps(['Analyzing resume...', 'Extracting skills...', 'Analyzing job description...', 'Calculating semantic similarity...', 'Finding skill gaps...', 'Generating recommendations...'], async () => {
      let job;
      if (file) { const fd = new FormData(); fd.append('file', file); job = await api('/api/job/upload', { method: 'POST', body: fd }); }
      else if (text) job = await api('/api/job/analyze', { method: 'POST', body: { text } });
      else job = await api('/api/job/samples/' + sample, { method: 'POST' });
      state.set('jobId', job.id);
      const m = await api('/api/match', { method: 'POST', body: { resume_id: +rid, job_id: job.id } });
      state.set('matchId', m.id);
      return { m, job };
    });
    renderMatch(m.m, m.job); toast('Match complete', 'success');
    res.scrollIntoView({ behavior: 'smooth' });
  } catch (e) { toast(e.message, 'error'); }
}

async function rankAll() {
  const rid = state.get('resumeId');
  if (!rid) return toast('Please upload a resume before running job matching.', 'error');
  try {
    const rows = await runSteps(['Analyzing job descriptions...', 'Calculating semantic similarity...', 'Ranking jobs...'], () => api('/api/match/rank', { method: 'POST', body: { resume_id: +rid, include_samples: true } }));
    document.getElementById('rank').innerHTML = `<div class="card-x"><h3><i class="fa-solid fa-ranking-star"></i> Job recommendations</h3><table class="tbl"><tr><th>#</th><th>Role</th><th>Score</th><th>Verdict</th><th>Matched</th><th>Missing</th><th>Preparation</th></tr>
     ${rows.map((r, i) => `<tr><td>${i + 1}</td><td><b>${esc(r.title)}</b></td><td><b>${r.score}%</b></td><td class="${labelClass(r.label)}">${esc(r.label)}</td><td class="small">${esc(r.matched.slice(0, 5).join(', ')) || '—'}</td><td class="small">${esc(r.missing.slice(0, 5).join(', ')) || '—'}</td><td class="small">${esc(r.preparation)}</td></tr>`).join('')}</table></div>`;
  } catch (e) { toast(e.message, 'error'); }
}

document.getElementById('analyze-btn').onclick = analyze;
document.getElementById('rank-btn').onclick = rankAll;
document.getElementById('sample').onchange = async function () {
  if (!this.value) return;
  const s = (await api('/api/job/samples')).find(j => j.id == this.value);
  if (s) document.getElementById('jd').value = s.text;
};
(async () => {
  try {
    const sel = document.getElementById('sample');
    (await api('/api/job/samples')).forEach(j => sel.insertAdjacentHTML('beforeend', `<option value="${j.id}">${esc(j.title)}</option>`));
    const mid = state.get('matchId');
    if (mid) { const m = await api('/api/match/' + mid); renderMatch(m, await api('/api/job/' + m.job_id)); }
  } catch { state.del('matchId'); }
})();
