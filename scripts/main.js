import { team } from '../data/team.js';
const scheduleResponse = await fetch('/data/schedule.json', { cache: 'no-cache' });
if (!scheduleResponse.ok) throw new Error('Не удалось загрузить расписание');
const schedule = await scheduleResponse.json();

const $ = (selector) => document.querySelector(selector);
const initials = (name) => name.split(' ').map((part) => part[0]).slice(0, 2).join('');
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

Object.entries(team.stats).forEach(([key, value]) => {
  const stat = $(`[data-stat="${key}"]`);
  if (stat) stat.textContent = value;
});

const nextGame = schedule.nextGame;
const displayDate = (date) => new Date(`${date}T12:00:00+03:00`).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Moscow' });
$('#next-game').innerHTML = `<p class="eyebrow">Следующая игра</p><div class="game-date">${displayDate(nextGame.dateISO)}<strong>${escapeHTML(nextGame.time)}</strong></div><p class="game-tournament">${escapeHTML(nextGame.tournament)}</p><div class="matchup"><span>Arena<br /><b>Play</b></span><i>VS</i><span>${escapeHTML(nextGame.opponent)}</span></div><p class="arena">⌖ ${escapeHTML(nextGame.arena)}</p>`;

const banner = $('#next-game-banner');
const videoCatalog = 'https://vkvideo.ru/@lhl_77/all';
const upcomingVideo = nextGame.videoUrl || videoCatalog;
banner.setAttribute('aria-label', `Ближайшая игра Arena Play: ${nextGame.opponent}, ${displayDate(nextGame.dateISO)} в ${nextGame.time}. Страница команды в ЛХЛ-77`);
banner.innerHTML = `<span><span class="live-dot"></span> Ближайшая игра</span><a href="https://lhl-77.ru/clubs/686" target="_blank" rel="noopener noreferrer"><strong>Arena Play — ${escapeHTML(nextGame.opponent)} · ${displayDate(nextGame.dateISO)}, ${escapeHTML(nextGame.time)}</strong></a><a class="banner-video" href="${escapeHTML(upcomingVideo)}" target="_blank" rel="noopener noreferrer">${upcomingVideo === videoCatalog ? 'Все видео ЛХЛ-77' : 'Смотреть трансляцию'} ↗</a>`;

$('#results-list').innerHTML = schedule.results.map((game) => {
  const videoUrl = game.videoUrl || videoCatalog;
  const videoLabel = videoUrl === videoCatalog ? 'Все видео ЛХЛ-77' : game.result === 'scheduled' ? 'Смотреть трансляцию' : 'Смотреть видео';
  return `<div class="result-row"><span>${escapeHTML(game.date)}</span><div class="result-match"><b>Arena Play — ${escapeHTML(game.opponent)}</b><a class="result-video" href="${escapeHTML(videoUrl)}" target="_blank" rel="noopener noreferrer">${videoLabel} ↗</a></div><strong class="${escapeHTML(game.result)}">${escapeHTML(game.score)}</strong></div>`;
}).join('');

const positionLabels = {'Вратари': 'Вратарь', 'Нападающие': 'Нападающий', 'Защитники': 'Защитник'};
$('#roster-list').innerHTML = Object.entries(team.roster).map(([position, players]) => `<div class="roster-group"><div class="roster-group-heading"><h3>${position}</h3><span>${players.length}</span></div>${players.map((player) => `<article class="player-card"><div class="player-avatar">${initials(player.name)}${player.photo ? `<img src="${escapeHTML(player.photo)}" alt="" loading="lazy" />` : ''}</div><div><h4>${player.name}${player.captain ? '<span class="captain-badge" aria-label="Капитан" title="Капитан">К</span>' : ''}${player.female ? '<span class="female-badge" role="img" aria-label="Девушка в команде" title="Валерия Головань">♥</span>' : ''}${player.badge ? `<span class="player-badge" role="img" aria-label="${escapeHTML(player.badge.label)}" title="${escapeHTML(player.badge.label)}">${escapeHTML(player.badge.icon)}</span>` : ''}</h4><span>${positionLabels[position]}</span></div><strong>#${player.number}</strong></article>`).join('')}</div>`).join('') + `<div class="coach-card"><div class="player-avatar">${initials(team.coach)}${team.coachPhoto ? `<img src="${escapeHTML(team.coachPhoto)}" alt="" loading="lazy" />` : ''}</div><span class="eyebrow">Главный тренер</span><strong>${team.coach}</strong></div>`;

document.querySelectorAll('.player-avatar img').forEach((image) => image.addEventListener('error', () => image.remove()));

$('#year').textContent = new Date().getFullYear();
document.querySelector('.menu-toggle').addEventListener('click', (event) => { const open = event.currentTarget.getAttribute('aria-expanded') === 'true'; event.currentTarget.setAttribute('aria-expanded', String(!open)); $('#site-nav').classList.toggle('is-open', !open); });
document.querySelectorAll('.site-nav a').forEach((link) => link.addEventListener('click', () => { $('#site-nav').classList.remove('is-open'); document.querySelector('.menu-toggle').setAttribute('aria-expanded', 'false'); }));
const contactDialog = $('#contact-dialog');
$('[data-captain-name]').textContent = team.contact.name;
const captainPhone = $('[data-captain-phone]');
captainPhone.textContent = team.contact.phone;
captainPhone.href = `tel:${team.contact.phone}`;
document.querySelectorAll('[data-contact-dialog]').forEach((link) => {
  link.addEventListener('click', (event) => {
    event.preventDefault();
    contactDialog.showModal();
  });
});
contactDialog.addEventListener('click', (event) => {
  const bounds = contactDialog.getBoundingClientRect();
  if (event.target === contactDialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) {
    contactDialog.close();
  }
});
