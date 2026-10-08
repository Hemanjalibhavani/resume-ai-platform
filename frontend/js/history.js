(async () => {
  try {
    const h = await api('/api/history');
    document.getElementById('matches').innerHTML = h.matches.length ? `<table class="tbl"><tr><th>#</th><th>Date</th><th>Candidate</th><th>Role</th><th>Score</th><th>Verdict</th><th></th></tr>${h.matches.map(m => `<tr><td>${m.id}</td><td class="small">${new Date(m.created_at + 'Z').toLocaleString()}</td><td>${esc(m.candidate)}</td><td>${esc(m.job_title)}</td><td><b>${m.score}%</b></td><td class="${labelClass(m.label)}">${esc(m.label)}</td><td><button class="btn-soft" onclick="openMatch(${m.id},${m.resume_id},${m.job_id})">View</button></td></tr>`).join('')}</table>` : '<p class="muted">No analyses yet. Run a job match to see it here.</p>';
    document.getElementById('interviews').innerHTML = h.interviews.length ? `<table class="tbl"><tr><th>Session</th><th>Date</th><th>Questions</th><th>Answered</th><th>Avg score</th></tr>${h.interviews.map(s => `<tr><td>${s.id}</td><td class="small">${new Date(s.created_at + 'Z').toLocaleString()}</td><td>${s.questions}</td><td>${s.answered}</td><td>${s.avg_score}/10</td></tr>`).join('')}</table>` : '<p class="muted">No interview sessions yet.</p>';
  } catch (e) { toast(e.message, 'error'); }
})();
function openMatch(id, rid, jid) { state.set('matchId', id); state.set('resumeId', rid); state.set('jobId', jid); location.href = 'job-matching.html'; }
