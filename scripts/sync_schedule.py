#!/usr/bin/env python3
"""Обновляет статическое расписание по странице Arena Play на сайте ЛХЛ-77."""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "data" / "schedule.json"
CLUB_URL = "https://lhl-77.ru/clubs/686"
MOSCOW = ZoneInfo("Europe/Moscow")
TEAM_NAME = "arena play"
SCORE_RE = re.compile(r"^\s*(\d+)\s*[:\-]\s*(\d+)\s*$")


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.heading = ""
        self.heading_text: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            if self.row is not None:
                self._finish_row()
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")
        elif tag in ("h3", "h4", "h5", "h6") and self.table is None:
            self.heading_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            self._finish_row()
        elif tag == "table" and self.table is not None:
            if self.row is not None:
                self._finish_row()
            self.tables.append({"heading": self.heading, "rows": self.table})
            self.table = None
        elif tag in ("h3", "h4", "h5", "h6") and self.heading_text is not None:
            self.heading = " ".join("".join(self.heading_text).split())
            self.heading_text = None

    def _finish_row(self) -> None:
        if self.row and self.table is not None:
            self.table.append(self.row)
        self.row = None

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        elif self.heading_text is not None:
            self.heading_text.append(data)


def normalize(value: str) -> str:
    return " ".join(value.replace("ё", "е").casefold().split())


def find_columns(rows: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    for row_index, row in enumerate(rows):
        labels = [normalize(cell) for cell in row]
        team_a = next((i for i, label in enumerate(labels) if "команда а" in label), None)
        team_b = next((i for i, label in enumerate(labels) if "команда б" in label), None)
        score = next((i for i, label in enumerate(labels) if "счет" in label or "счёт" in label), None)
        date_col = next((i for i, label in enumerate(labels) if label in ("число", "дата")), None)
        time_col = next((i for i, label in enumerate(labels) if "время" in label), None)
        arena = next((i for i, label in enumerate(labels) if "каток" in label or "арена" in label), None)
        division = next((i for i, label in enumerate(labels) if "дивизион" in label or "турнир" in label), None)
        if None not in (team_a, team_b, score, date_col, time_col, arena):
            return row_index, {"team_a": team_a, "team_b": team_b, "score": score,
                               "date": date_col, "time": time_col, "arena": arena,
                               "division": division}
    return None


def parse_date(value: str) -> date | None:
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    return None


def parse_games(page: str) -> list[dict]:
    parser = TableParser()
    parser.feed(page)
    games: list[dict] = []
    for table in parser.tables:
        header = find_columns(table["rows"])
        if not header:
            continue
        header_index, columns = header
        for cells in table["rows"][header_index + 1:]:
            if max(i for i in columns.values() if i is not None) >= len(cells):
                continue
            team_a = cells[columns["team_a"]].strip()
            team_b = cells[columns["team_b"]].strip()
            a_is_team = normalize(team_a) == TEAM_NAME
            b_is_team = normalize(team_b) == TEAM_NAME
            if a_is_team == b_is_team:
                continue
            game_date = parse_date(cells[columns["date"]])
            if not game_date:
                continue
            game_time = cells[columns["time"]].strip()
            if not re.fullmatch(r"\d{1,2}:\d{2}", game_time):
                continue
            score_match = SCORE_RE.fullmatch(cells[columns["score"]])
            score = None
            result = None
            if score_match:
                a_score, b_score = map(int, score_match.groups())
                own, opponent_score = (a_score, b_score) if a_is_team else (b_score, a_score)
                score = f"{own} : {opponent_score}"
                result = "win" if own > opponent_score else "loss" if own < opponent_score else "draw"
            division_col = columns["division"]
            tournament = cells[division_col].strip() if division_col is not None and division_col < len(cells) else ""
            if not tournament and table["heading"]:
                tournament = table["heading"].split("/")[-1].replace("(смотреть)", "").strip()
            games.append({
                "date": game_date.strftime("%d.%m.%Y"),
                "dateISO": game_date.isoformat(),
                "time": game_time.zfill(5),
                "arena": cells[columns["arena"]].strip(),
                "opponent": team_b if a_is_team else team_a,
                "score": score,
                "result": result,
                "tournament": tournament or table["heading"] or "ЛХЛ-77",
                "isUpcomingTable": normalize(table["heading"]) == "ближайшие игры",
            })
    return games


def game_key(game: dict) -> tuple[str, str]:
    return game.get("dateISO", ""), normalize(game.get("opponent", ""))


def update_schedule(current: dict, games: list[dict], now: datetime) -> dict:
    current_results = current.get("results", [])
    prior_by_key = {game_key(game): game for game in current_results}
    moment = now.astimezone(MOSCOW)
    upcoming = []
    completed = []
    for game in games:
        starts = datetime.combine(date.fromisoformat(game["dateISO"]),
                                  time.fromisoformat(game["time"]), tzinfo=MOSCOW)
        if starts > moment:
            upcoming.append(game)
        elif not game.get("isUpcomingTable") and game["score"] is not None:
            completed.append(game)
    upcoming.sort(key=lambda game: (game["dateISO"], game["time"]))
    next_source = upcoming[0] if upcoming else None

    def result_record(game: dict, status: str) -> dict:
        old = prior_by_key.get(game_key(game), {})
        return {
            "date": game["date"],
            "dateISO": game["dateISO"],
            "opponent": game["opponent"],
            "score": game["score"] if status != "scheduled" else "0 : 0",
            "result": game["result"] if status != "scheduled" else "scheduled",
            "tournament": game["tournament"],
            "videoUrl": old.get("videoUrl"),
        }

    history_by_key: dict[tuple[str, str], dict] = {}
    for old in current_results:
        if old.get("result") != "scheduled":
            history_by_key[game_key(old)] = old
    for game in completed:
        history_by_key[game_key(game)] = result_record(game, "finished")
    history = sorted(history_by_key.values(), key=lambda game: game.get("dateISO", ""), reverse=True)

    if next_source:
        next_game = {key: next_source[key] for key in ("date", "dateISO", "time", "arena", "opponent", "tournament")}
        pending = result_record(next_source, "scheduled")
        # Сохраняем прежний матч до публикации ЛХЛ-77 итогового счёта.
        for old in current_results:
            if old.get("result") == "scheduled" and game_key(old) != game_key(pending):
                if game_key(old) not in history_by_key:
                    history.append(old)
        history.sort(key=lambda game: game.get("dateISO", ""), reverse=True)
        results = [pending, *history[:2]]
    else:
        next_game = current["nextGame"]
        results = history[:3]
        for old in current_results:
            if old.get("result") == "scheduled" and game_key(old) not in history_by_key:
                results.append(old)
        results = sorted(results, key=lambda game: game.get("dateISO", ""), reverse=True)[:3]
    return {"nextGame": next_game, "results": results}


def fetch_page() -> str:
    request = Request(CLUB_URL, headers={"User-Agent": "ArenaPlayScheduleBot/1.0 (+https://arenaplayteam.ru)"})
    with urlopen(request, timeout=25) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset)


def main() -> int:
    try:
        page = fetch_page()
        games = parse_games(page)
        if not games:
            raise RuntimeError("На странице не найдена таблица игр Arena Play; расписание не изменено")
        current = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
        updated = update_schedule(current, games, datetime.now(MOSCOW))
        serialized = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
        if serialized != SCHEDULE_PATH.read_text(encoding="utf-8"):
            SCHEDULE_PATH.write_text(serialized, encoding="utf-8")
            print("Расписание команды обновлено.")
        else:
            print("Расписание не изменилось.")
        return 0
    except Exception as error:
        print(f"Ошибка обновления расписания: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
