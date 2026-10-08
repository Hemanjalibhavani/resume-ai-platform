/* Chart.js helpers + dashboard logic. */
const _charts = {};
const PALETTE = ['#4f46e5', '#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899'];
function mkChart(id, type, labels, datasets, opts = {}) {
  const el = document.getElementById(id);
  if (!el || typeof Chart === 'undefined') return;
  _charts[id]?.destroy();
  _charts[id] = new Chart(el, { type, data: { labels, datasets }, options: Object.assign({ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: type === 'doughnut' } } }, opts) });
}
const barChart = (id, labels, data, opts = {}) => mkChart(id, 'bar', labels, [{ data, backgroundColor: '#6366f1', borderRadius: 8 }], Object.assign({ scales: { y: { beginAtZero: true } } }, opts));
const lineChart = (id, labels, data, max = 100) => mkChart(id, 'line', labels, [{ data, borderColor: '#7c3aed', backgroundColor: 'rgba(124,58,237,.12)', fill: true, tension: .35 }], { scales: { y: { beginAtZero: true, max } } });
const doughnut = (id, labels, data) => mkChart(id, 'doughnut', labels, [{ data, backgroundColor: PALETTE }]);
const hbar = (id, labels, data, colors) => mkChart(id, 'bar', labels, [{ data, backgroundColor: colors || '#6366f1', borderRadius: 6 }], { indexAxis: 'y', scales: { x: { beginAtZero: true, max: 100 } } });

async function initDashboard() {
  const d = await api('/api/dashboard');
  const t = d.totals;
  const cards = [['fa-file-lines', 'Resumes Analyzed', t.resumes], ['fa-briefcase', 'Jobs Analyzed', t.jobs],
    ['fa-percent', 'Average Match Score', t.average_score + '%'], ['fa-circle-check', 'Skills Matched', t.skills_matched]];
  document.getElementById('stats').innerHTML = cards.map(c => `<div class="card-x stat"><div class="ico"><i class="fa-solid ${c[0]}"></i></div><div><div class="num">${c[2]}</div><div class="muted small">${c[1]}</div></div></div>`).join('');
  document.getElementById('highlights').innerHTML = `${badge('Top skill: ' + t.top_skill, 'badge-ok')}${badge('Biggest skill gap: ' + t.biggest_gap, 'badge-miss')}`;
  barChart('c-scores', d.match_scores.map(x => x.label), d.match_scores.map(x => x.score), { scales: { y: { beginAtZero: true, max: 100 } } });
  doughnut('c-skills', d.skills_distribution.map(x => x.category.replace('_', ' ')), d.skills_distribution.map(x => x.count));
  barChart('c-gap', d.skill_gap.map(x => x.skill), d.skill_gap.map(x => x.count));
  barChart('c-jobs', d.jobs_analyzed.map(x => x.title.slice(0, 18)), d.jobs_analyzed.map((x, i) => i + 1));
  lineChart('c-history', d.score_history.map(x => x.label), d.score_history.map(x => x.score));
  lineChart('c-interview', d.interview_performance.map(x => x.label), d.interview_performance.map(x => x.score), 10);
  document.getElementById('recent-resumes').innerHTML = d.recent_resumes.length ? d.recent_resumes.map(r => `<li><i class="fa-solid fa-file-pdf" style="color:var(--p1)"></i><span>${esc(r.name)} <span class="muted small">${esc(r.file)}</span></span><b style="margin-left:auto">${r.score}/100</b></li>`).join('') : '<li class="muted">No resumes yet.</li>';
  document.getElementById('recent-matches').innerHTML = d.recent_matches.length ? d.recent_matches.map(m => `<li><i class="fa-solid fa-bullseye" style="color:var(--p2)"></i><span class="${labelClass(m.label)}">${esc(m.label)}</span><b style="margin-left:auto">${m.score}%</b></li>`).join('') : '<li class="muted">No analyses yet.</li>';
  const rid = state.get('resumeId');
  if (rid) {
    const rec = await api('/api/recommendations?resume_id=' + rid);
    document.getElementById('recs').innerHTML = rec.recommendations.length ? rec.recommendations.map(r => `<li><i class="fa-solid fa-lightbulb" style="color:var(--warn)"></i><span>${esc(r.text)}</span></li>`).join('') : '<li class="muted">Run a job match to get recommendations.</li>';
  }
}
