const out = document.getElementById('result');
function renderResume(r) {
  const comp = r.completeness;
  const bycat = {};
  Object.entries(r.skills).forEach(([k, v]) => (bycat[v.category] = bycat[v.category] || []).push(k));
  const catName = { language: 'Programming languages', framework: 'Frameworks & libraries', database: 'Databases', cloud_tool: 'Tools & cloud', concept: 'Concepts' };
  const entries = list => list.length ? list.map(e => `<li><i class="fa-solid fa-angle-right"></i><span><b>${esc(e.title)}</b>${e.meta ? ' <span class="badge-x">' + esc(e.meta) + '</span>' : ''}${e.description ? '<br><span class="muted small">' + esc(e.description) + '</span>' : ''}</span></li>`).join('') : '<li class="muted">Not detected</li>';
  const lines = list => list.length ? list.map(e => `<li><i class="fa-solid fa-angle-right"></i><span>${esc(e)}</span></li>`).join('') : '<li class="muted">Not detected</li>';
  out.innerHTML = `
  <div class="grid g-main">
   <div class="card-x"><h3><i class="fa-solid fa-user"></i> ${esc(r.candidate_name)}</h3>
     <p class="muted small">${esc(r.filename)}</p>
     <p><i class="fa-solid fa-envelope"></i> ${esc(r.email) || '—'} &nbsp; <i class="fa-solid fa-phone"></i> ${esc(r.phone) || '—'}</p>
     <p class="small muted">${r.linkedin ? esc(r.linkedin) + ' ' : ''}${r.github ? esc(r.github) : ''}</p>
     <h4>Education</h4><ul class="clean">${lines(r.education)}</ul></div>
   <div class="card-x" style="text-align:center"><h3>Resume Score</h3><div style="display:flex;justify-content:center">${ring(comp.score)}</div>
     <p class="muted small" style="margin-top:.6rem">Completeness: ${comp.score}/100</p></div>
  </div>
  <div class="grid g2">
   <div class="card-x"><h3>Sections detected</h3><ul class="clean">${comp.detected.map(d => `<li class="good"><i class="fa-solid fa-check"></i>${esc(d)}</li>`).join('')}${comp.missing.map(d => `<li class="bad"><i class="fa-solid fa-triangle-exclamation"></i>${esc(d)} (missing)</li>`).join('')}</ul></div>
   <div class="card-x"><h3>Skills (${Object.keys(r.skills).length})</h3>${Object.entries(bycat).map(([c, l]) => `<div class="small muted">${catName[c] || c}</div><div>${l.map(s => badge(pretty(s))).join('')}</div>`).join('') || '<p class="muted">No skills detected</p>'}</div>
  </div>
  <div class="grid g2">
   <div class="card-x"><h3>Projects</h3><ul class="clean">${entries(r.projects)}</ul></div>
   <div class="card-x"><h3>Internships &amp; Experience</h3><ul class="clean">${entries(r.internships.concat(r.experience))}</ul>
     <h4 style="margin-top:1rem">Certifications</h4><ul class="clean">${lines(r.certifications)}</ul></div>
  </div>
  <div id="ats"></div><div id="improve"></div>
  <div class="card-x"><a class="btn-grad" href="job-matching.html"><i class="fa-solid fa-bullseye"></i> Match with a job</a></div>`;
  loadAnalysis(r.id);
}

async function loadAnalysis(id) {
  try {
    const a = await api('/api/resume/analyze', { method: 'POST', body: { resume_id: id, job_id: state.get('jobId') ? +state.get('jobId') : null } });
    const t = a.ats;
    document.getElementById('ats').innerHTML = `<div class="card-x"><h3><i class="fa-solid fa-robot"></i> ATS Analysis</h3>
      <div style="display:flex;gap:1.5rem;flex-wrap:wrap;align-items:center">${ring(t.score, true)}
      <div style="flex:1;min-width:240px"><b>${t.score}/100</b> <span class="muted small">${esc(t.label)}</span>
      ${Object.entries(t.breakdown).map(([k, v]) => `<div class="bar-row"><span>${esc(k.replace(/_/g, ' '))}</span>${bar(v[0], v[1])}<small>${v[0]}/${v[1]}</small></div>`).join('')}</div></div>
      ${t.issues.length ? '<h4>Issues</h4><ul class="clean">' + t.issues.map(i => `<li class="bad"><i class="fa-solid fa-triangle-exclamation"></i>${esc(i)}</li>`).join('') + '</ul>' : ''}
      ${t.tips.length ? '<ul class="clean">' + t.tips.map(i => `<li><i class="fa-solid fa-lightbulb"></i>${esc(i)}</li>`).join('') + '</ul>' : ''}
      <p class="muted small">${esc(t.disclaimer)}</p></div>`;
    document.getElementById('improve').innerHTML = `<div class="card-x"><h3><i class="fa-solid fa-wand-magic-sparkles"></i> Improve My Resume</h3>${a.improvements.length ? a.improvements.map(i => `
      <div class="ba"><div class="before"><b>Original</b>${esc(i.original)}<div class="small muted" style="margin-top:.3rem">${i.issues.map(esc).join(' · ')}</div></div><div class="after"><b>Suggested</b>${esc(i.suggested)}</div></div>`).join('') : '<p class="muted">No weak bullet points found.</p>'}</div>`;
  } catch (e) { toast(e.message, 'error'); }
}

async function uploadFile(file) {
  if (!file) return;
  const fd = new FormData(); fd.append('file', file);
  try {
    const r = await runSteps(['Analyzing resume...', 'Extracting skills...', 'Detecting sections...'], () => api('/api/resume/upload', { method: 'POST', body: fd }));
    state.set('resumeId', r.id); state.del('matchId');
    toast('Resume analyzed', 'success'); renderResume(r);
  } catch (e) { toast(e.message, 'error'); }
}

async function loadList() {
  const rows = await api('/api/resumes');
  out.innerHTML = `<div class="card-x"><h3>My Resumes</h3>${rows.length ? `<table class="tbl"><tr><th>ID</th><th>Candidate</th><th>File</th><th>Score</th><th>Skills</th><th></th></tr>${rows.map(r => `<tr><td>${r.id}</td><td>${esc(r.candidate_name)}</td><td>${esc(r.filename)}</td><td>${r.score}/100</td><td>${r.skills}</td><td><button class="btn-soft" onclick="openResume(${r.id})">Open</button></td></tr>`).join('')}</table>` : '<p class="muted">No resumes uploaded yet.</p>'}</div>`;
}
async function openResume(id) { state.set('resumeId', id); renderResume(await api('/api/resume/' + id)); }

const dz = document.getElementById('dropzone'), fi = document.getElementById('file');
dz.onclick = () => fi.click();
fi.onchange = () => uploadFile(fi.files[0]);
['dragover', 'dragenter'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.add('drag'); }));
['dragleave', 'drop'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.remove('drag'); }));
dz.addEventListener('drop', ev => uploadFile(ev.dataTransfer.files[0]));
document.getElementById('demo-btn').onclick = async () => {
  try { const r = await api('/api/resume/demo', { method: 'POST' }); state.set('resumeId', r.id); state.del('matchId'); renderResume(r); toast('Demo resume loaded', 'success'); }
  catch (e) { toast(e.message, 'error'); }
};
(async () => {
  if (location.hash === '#list') return loadList();
  const id = state.get('resumeId');
  if (id) { try { renderResume(await api('/api/resume/' + id)); } catch { state.del('resumeId'); } }
})();
window.addEventListener('hashchange', () => location.reload());
