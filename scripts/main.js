import { team } from '../data/team.js';

const $ = (selector) => document.querySelector(selector);
const initials = (name) => name.split(' ').map((part) => part[0]).slice(0, 2).join('');

for (const [key, value] of Object.entries(team.stats)) {
  const element = document.querySelector(`[data-stat="${key}"]`);
  if (element) element.textContent = value;
}

$('#next-game').innerHTML = `<p class="eyebrow">Следующая игра</p><div class="game-date">${team.nextGame.date}<strong>${team.nextGame.time}</strong></div><p class="game-tournament">${team.nextGame.tournament}</p><div class="matchup"><span>Arena<br /><b>Play</b></span><i>VS</i><span>${team.nextGame.opponent}</span></div><p class="arena">⌖ ${team.nextGame.arena}</p>`;

$('#results-list').innerHTML = team.results.map((game) => `<div class="result-row"><span>${game.date}</span><b>Arena Play — ${game.opponent}</b><strong class="${game.result}">${game.score}</strong></div>`).join('');

$('#roster-list').innerHTML = Object.entries(team.roster).map(([position, players]) => `<div class="roster-group"><div class="roster-group-heading"><h3>${position}</h3><span>${players.length}</span></div>${players.map((player) => `<article class="player-card"><div class="player-avatar">${initials(player.name)}</div><div><h4>${player.name}</h4><span>${position.slice(0, -1)}</span></div><strong>#${player.number}</strong></article>`).join('')}</div>`).join('') + `<div class="coach-card"><span class="eyebrow">Главный тренер</span><strong>${team.coach}</strong></div>`;

$('#year').textContent = new Date().getFullYear();
document.querySelector('.menu-toggle').addEventListener('click', (event) => { const open = event.currentTarget.getAttribute('aria-expanded') === 'true'; event.currentTarget.setAttribute('aria-expanded', String(!open)); $('#site-nav').classList.toggle('is-open', !open); });
document.querySelectorAll('.site-nav a').forEach((link) => link.addEventListener('click', () => { $('#site-nav').classList.remove('is-open'); document.querySelector('.menu-toggle').setAttribute('aria-expanded', 'false'); }));
document.querySelectorAll('[data-placeholder-link]').forEach((link) => link.addEventListener('click', (event) => { event.preventDefault(); }));

