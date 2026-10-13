import { team } from '../data/team.js';
const scheduleResponse = await fetch('/data/schedule.json', { cache: 'no-cache' });
if (!scheduleResponse.ok) throw new Error('Не удалось загрузить расписание');
const schedule = await scheduleResponse.json();

const $ = (selector) => document.querySelector(selector);
const initials = (name) => name.split(' ').map((part) => part[0]).slice(0, 2).join('');
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

const nextGame = schedule.nextGame;
const displayDate = (date) => new Date(`${date}T12:00:00+03:00`).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Moscow' });
$('#next-game').innerHTML = `<p class="eyebrow">Следующая игра</p><div class="game-date">${displayDate(nextGame.dateISO)}<strong>${escapeHTML(nextGame.time)}</strong></div><p class="game-tournament">${escapeHTML(nextGame.tournament)}</p><div class="matchup"><span>Arena<br /><b>Play</b></span><i>VS</i><span>${escapeHTML(nextGame.opponent)}</span></div><p class="arena">⌖ ${escapeHTML(nextGame.arena)}</p>`;

const banner = $('#next-game-banner');
banner.href = 'https://lhl-77.ru/clubs/686';
banner.setAttribute('aria-label', `Ближайшая игра Arena Play: ${nextGame.opponent}, ${displayDate(nextGame.dateISO)} в ${nextGame.time}. Страница команды в ЛХЛ-77`);
banner.innerHTML = `<span><span class="live-dot"></span> Ближайшая игра</span><strong>Arena Play — ${escapeHTML(nextGame.opponent)} · ${displayDate(nextGame.dateISO)}, ${escapeHTML(nextGame.time)}</strong><span aria-hidden="true">↗</span>`;

$('#results-list').innerHTML = schedule.results.map((game) => `<div class="result-row"><span>${escapeHTML(game.date)}</span><div class="result-match"><b>Arena Play — ${escapeHTML(game.opponent)}</b>${game.videoUrl ? `<a class="result-video" href="${escapeHTML(game.videoUrl)}" target="_blank" rel="noopener noreferrer">Смотреть видео ↗</a>` : game.result === 'scheduled' ? '<span class="result-video-pending">Видео пока нет</span>' : ''}</div><strong class="${escapeHTML(game.result)}">${escapeHTML(game.score)}</strong></div>`).join('');

$('#roster-list').innerHTML = Object.entries(team.roster).map(([position, players]) => `<div class="roster-group"><div class="roster-group-heading"><h3>${position}</h3><span>${players.length}</span></div>${players.map((player) => `<article class="player-card"><div class="player-avatar">${initials(player.name)}</div><div><h4>${player.name}</h4><span>${position.slice(0, -1)}</span></div><strong>#${player.number}</strong></article>`).join('')}</div>`).join('') + `<div class="coach-card"><span class="eyebrow">Главный тренер</span><strong>${team.coach}</strong></div>`;

$('#year').textContent = new Date().getFullYear();
document.querySelector('.menu-toggle').addEventListener('click', (event) => { const open = event.currentTarget.getAttribute('aria-expanded') === 'true'; event.currentTarget.setAttribute('aria-expanded', String(!open)); $('#site-nav').classList.toggle('is-open', !open); });
document.querySelectorAll('.site-nav a').forEach((link) => link.addEventListener('click', () => { $('#site-nav').classList.remove('is-open'); document.querySelector('.menu-toggle').setAttribute('aria-expanded', 'false'); }));
document.querySelectorAll('[data-placeholder-link]').forEach((link) => link.addEventListener('click', (event) => { event.preventDefault(); }));
