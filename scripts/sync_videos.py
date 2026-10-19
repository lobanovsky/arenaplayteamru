"""Находит записи матчей в публичном каталоге VK Видео."""

import json
import re
from datetime import date, timedelta
from html import unescape
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener

VIDEO_CATALOG = "https://vkvideo.ru/@lhl_77/all"
OWNER_CATALOG = "https://vkvideo.ru/videos-71330880"


class VideoParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.script = None
        self.videos = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.script = []

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            try:
                self.collect(json.loads("".join(self.script)))
            except (ValueError, TypeError):
                pass
            self.script = None

    def collect(self, value):
        if isinstance(value, list):
            for item in value:
                self.collect(item)
        elif isinstance(value, dict):
            if value.get("@type") == "VideoObject":
                url = next((candidate for candidate in (value.get("url", ""), value.get("contentUrl", ""))
                            if re.fullmatch(r"https://vkvideo\.ru/(?:video|live)-71330880_\d+", candidate)), "")
                publication = value.get("publication", {})
                if not isinstance(publication, dict):
                    publication = {}
                if re.fullmatch(r"https://vkvideo\.ru/(?:video|live)-71330880_\d+", url):
                    self.videos.append({"title": unescape(value.get("name", "")), "url": url,
                                        "date": publication.get("startDate") or value.get("startDate") or value.get("datePublished") or value.get("uploadDate", "")})
            for child in value.values():
                if isinstance(child, (dict, list)):
                    self.collect(child)


def parse_videos(page):
    parser = VideoParser()
    parser.feed(page)
    return parser.videos


def title_key(value):
    value = value.casefold().replace("ё", "е")
    value = re.sub(r"\bvs\.?\b", " ", value)
    return " ".join(re.findall(r"[a-zа-я0-9]+", value))


def find_video(game, videos):
    opponent = title_key(game["opponent"])
    names = {f"arena play {opponent}", f"{opponent} arena play"}
    game_date = date.fromisoformat(game["dateISO"])
    candidates = {}
    for video in videos:
        if title_key(video["title"]) not in names:
            continue
        try:
            published = date.fromisoformat(video["date"][:10])
        except ValueError:
            continue
        # Старые встречи тех же команд не считаем трансляцией нового матча.
        if game_date - timedelta(days=3) <= published <= game_date + timedelta(days=1):
            candidates[video["url"]] = abs((published - game_date).days)
    if not candidates:
        return None
    best_distance = min(candidates.values())
    best = [url for url, distance in candidates.items() if distance == best_distance]
    return best[0] if len(best) == 1 else None


def fetch_videos():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    videos = []
    errors = []
    for url in (VIDEO_CATALOG, OWNER_CATALOG):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
        try:
            with opener.open(request, timeout=25) as response:
                charset = response.headers.get_content_charset() or "windows-1251"
                videos.extend(parse_videos(response.read().decode(charset)))
        except Exception as error:
            errors.append(str(error))
    if not videos and errors:
        raise RuntimeError("; ".join(errors))
    return videos


def attach_videos(schedule, videos):
    matches = [*schedule.get("allMatches", []), *schedule["results"]]
    for game in matches:
        if not game.get("videoUrl") or game["videoUrl"] == VIDEO_CATALOG:
            game["videoUrl"] = find_video(game, videos) or VIDEO_CATALOG
    upcoming = schedule["nextGame"]
    matching = next((game for game in matches
                     if game["dateISO"] == upcoming["dateISO"]
                     and title_key(game["opponent"]) == title_key(upcoming["opponent"])), None)
    upcoming["videoUrl"] = (matching or {}).get("videoUrl") or find_video(upcoming, videos) or upcoming.get("videoUrl") or VIDEO_CATALOG
