let questions = [], idx = 0;
const list = document.getElementById('list'), practice = document.getElementById('practice');
async function loadCats() {
  const cats = await api('/api/interview/categories');
  document.getElementById('cats').innerHTML = cats.map(c => `<label class="badge-x" style="cursor:pointer"><input type="checkbox" value="${esc(c)}"> ${esc(c)}</label>`).join('');
}
function renderQs() {
  list.innerHTML = questions.map(q => `<details class="q"><summary>${badge(q.category)}${badge(q.difficulty, q.difficulty === 'Hard' ? 'badge-miss' : q.difficulty === 'Easy' ? 'badge-ok' : 'badge-part')} ${esc(q.question)}</summary>
   <p class="small"><b>Expected concepts:</b> ${q.expected_concepts.map(c => badge(c)).join('')}</p>
   <p class="small"><b>Follow-ups:</b> ${q.follow_ups.map(esc).join(' · ') || '—'}</p>
   ${q.sample_answer ? `<p class="small"><b>Sample answer:</b> ${esc(q.sample_answer)}</p>` : ''}</details>`).join('');
  document.getElementById('start').classList.toggle('hidden', !questions.length);
}
async function generate() {
  const rid = state.get('resumeId');
  if (!rid) return toast('Please upload a resume before running job matching.', 'error');
  const cats = [...document.querySelectorAll('#cats input:checked')].map(i => i.value);
  try {
    const r = await runSteps(['Reading resume...', 'Analyzing job requirements...', 'Generating questions...'], () => api('/api/interview/generate', { method: 'POST', body: { resume_id: +rid, job_id: state.get('jobId') ? +state.get('jobId') : null, categories: cats.length ? cats : null, count: +document.getElementById('count').value || 12, with_answers: document.getElementById('answers').checked } }));
    questions = r.questions; idx = 0; renderQs(); practice.classList.add('hidden'); toast(`${questions.length} questions generated`, 'success');
  } catch (e) { toast(e.message, 'error'); }
}
function showQ() {
  const q = questions[idx];
  if (!q) { practice.innerHTML = '<div class="card-x"><h3>Interview complete 🎉</h3><p class="muted">Check the dashboard for your interview performance chart.</p></div>'; return; }
  practice.innerHTML = `<div class="card-x"><div class="muted small">Question ${idx + 1} of ${questions.length} · ${esc(q.category)} · ${esc(q.difficulty)}</div>
   <h3>${esc(q.question)}</h3><textarea id="ans" rows="5" placeholder="Type your answer..."></textarea>
   <div style="margin-top:.7rem"><button class="btn-grad" id="submit"><i class="fa-solid fa-paper-plane"></i> Submit answer</button> <button class="btn-line" id="skip">Skip</button></div><div id="fb"></div></div>`;
  document.getElementById('skip').onclick = () => { idx++; showQ(); };
  document.getElementById('submit').onclick = async () => {
    const a = document.getElementById('ans').value.trim();
    if (!a) return toast('Please type an answer first.', 'error');
    try {
      const r = await api('/api/interview/evaluate', { method: 'POST', body: { question_id: q.id, answer: a } });
      document.getElementById('fb').innerHTML = `<hr><div style="display:flex;gap:1rem;align-items:center">${ring(r.score * 10, true).replace(/>(\d+)</, `>${r.score}/10<`)}<div><b>Score: ${r.score}/10</b> <span class="muted small">(${r.mode} evaluation)</span></div></div>
       <ul class="clean good">${r.positives.map(p => `<li><i class="fa-solid fa-check"></i>${esc(p)}</li>`).join('')}</ul>
       <ul class="clean bad">${r.improvements.map(p => `<li><i class="fa-solid fa-triangle-exclamation"></i>${esc(p)}</li>`).join('')}</ul>
       <p><b>Improvement suggestion:</b> ${esc(r.suggestion)}</p>
       <button class="btn-grad" id="next">${idx + 1 < questions.length ? 'Next question' : 'Finish'}</button>`;
      document.getElementById('submit').disabled = true;
      document.getElementById('next').onclick = () => { idx++; showQ(); };
    } catch (e) { toast(e.message, 'error'); }
  };
}
document.getElementById('gen').onclick = generate;
document.getElementById('start').onclick = () => { idx = 0; practice.classList.remove('hidden'); showQ(); practice.scrollIntoView({ behavior: 'smooth' }); };
loadCats();
