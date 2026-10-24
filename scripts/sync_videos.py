"""Находит записи матчей в публичных каталогах Rutube и VK Видео."""

import json
import re
import sys
from datetime import date, timedelta
from html import unescape
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener

VIDEO_CATALOG = "https://vkvideo.ru/@lhl_77/all"
OWNER_CATALOG = "https://vkvideo.ru/videos-71330880"
RUTUBE_API = "https://rutube.ru/api/video/person/35268475/"


def parse_rutube_videos(payload):
    videos = []
    for item in payload.get("results", []):
        url = item.get("video_url", "")
        if (item.get("author", {}).get("id") != 35268475
                or item.get("is_deleted") or item.get("is_hidden")
                or not re.fullmatch(r"https://rutube\.ru/video/[a-f0-9]{32}/", url)):
            continue
        videos.append({"title": item.get("title", ""), "url": url,
                       "date": item.get("publication_ts") or item.get("created_ts", "")})
    return videos


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
    rutube = [url for url in best if url.startswith("https://rutube.ru/video/")]
    if rutube:
        best = rutube
    return best[0] if len(best) == 1 else None


def fetch_videos():
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    videos = []
    errors = []
    # Ограничиваем глубину каталога, чтобы обновление не обходило весь архив лиги.
    for page in range(1, 4):
        try:
            with opener.open(Request(f"{RUTUBE_API}?page={page}", headers={"User-Agent": "ArenaPlayScheduleBot/1.0"}), timeout=25) as response:
                payload = json.loads(response.read().decode("utf-8"))
            videos.extend(parse_rutube_videos(payload))
            if not payload.get("has_next"):
                break
        except Exception as error:
            errors.append(f"Rutube: {error}")
            break
    for url in (VIDEO_CATALOG, OWNER_CATALOG):
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"})
        try:
            with opener.open(request, timeout=25) as response:
                charset = response.headers.get_content_charset() or "windows-1251"
                videos.extend(parse_videos(response.read().decode(charset)))
        except Exception as error:
            errors.append(str(error))
    if not videos:
        raise RuntimeError("; ".join(errors) or "В каталогах Rutube и VK Видео не найдены метаданные видео")
    if errors:
        print("Часть каталогов видео недоступна: " + "; ".join(errors), file=sys.stderr)
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
