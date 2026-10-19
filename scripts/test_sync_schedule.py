import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from sync_schedule import parse_games, update_schedule


MOSCOW = ZoneInfo("Europe/Moscow")


def row(date, time, arena, team_a, score, team_b, division="ДЕБЮТАНТ"):
    return (f"<tr><td>1</td><td>1</td><td>{division}</td><td>{date}</td>"
            f"<td>Сб</td><td>{time}</td><td>{arena}</td><td>{team_a}</td>"
            f"<td>{score}</td><td>{team_b}</td></tr>")


def page(upcoming, completed=()):
    return """<html><body><h4>Ближайшие игры</h4><table><tr>
      <th>Тур</th><th>Круг</th><th>Дивизион</th><th>Число</th><th>Дн</th>
      <th>Время</th><th>Каток</th><th>Команда А</th><th>Счет</th><th>Команда Б</th>
    </tr>""" + "".join(upcoming) + """</table><h6>СЕЗОН / ДЕБЮТАНТ</h6><table><tr>
      <th>Тур</th><th>Круг</th><th>Число</th><th>Дн</th><th>Время</th>
      <th>Каток</th><th>Команда А</th><th>Счет</th><th>Команда Б</th>
    </tr>""" + "".join(game.replace("<td>ДЕБЮТАНТ</td>", "") for game in completed) + """</table></body></html>"""


class ScheduleSyncTests(unittest.TestCase):
    def test_full_archive_keeps_qualification_and_every_upcoming_match(self):
        current = {"nextGame": {}, "results": []}
        games = parse_games(page(
            [row("24/10/2026", "20:15", "Лёд", "Arena Play", "0:0", "Первый"),
             row("31/10/2026", "19:00", "Лёд", "Arena Play", "0:0", "Второй")],
            [row("17/10/2026", "21:45", "Арена", "Arena Play", "2:10", "Легенда"),
             row("11/10/2026", "18:15", "Арена", "Arena Play", "1:2", "Grizzly team"),
             row("03/10/2026", "09:45", "Арена", "Arena Play", "3:6", "Крылья"),
             row("12/09/2026", "21:45", "Арена", "ФедКо", "3:5", "Arena Play")],
        ))
        games[-1]["tournament"] = "КВАЛИФИКАЦИЯ"
        updated = update_schedule(current, games, datetime(2026, 10, 19, 7, tzinfo=MOSCOW))
        self.assertEqual(len(updated["results"]), 3)
        self.assertEqual(len(updated["allMatches"]), 6)
        self.assertEqual(sum(game["result"] == "scheduled" for game in updated["allMatches"]), 2)
        qualification = next(game for game in updated["allMatches"] if game["tournament"] == "КВАЛИФИКАЦИЯ")
        self.assertEqual(qualification["score"], "5 : 3")
        self.assertEqual(qualification["result"], "win")
        self.assertEqual(qualification["time"], "21:45")
        # Повторная синхронизация не обрезает архив и не теряет старую ссылку на видео.
        qualification["videoUrl"] = "https://vkvideo.ru/video-71330880_123"
        again = update_schedule(updated, games[:3], datetime(2026, 10, 19, 13, tzinfo=MOSCOW))
        archived = next(game for game in again["allMatches"] if game["opponent"] == "ФедКо")
        self.assertEqual(archived["videoUrl"], qualification["videoUrl"])
        self.assertEqual(len(again["allMatches"]), 6)

    def test_parse_home_and_away_rows_and_scores_from_team_perspective(self):
        games = parse_games(page(
            [row("17/10/2026", "21:45", "АПИА АРЕНА-2", "Arena Play", "", "ЛЕГЕНДА-СТАРТ")],
            [row("11/10/2026", "18:15", "Созвездие", "Arena Play", "1:2", "Grizzly team"),
             row("03/10/2026", "09:45", "Академия льда", "Крылья Столицы", "3:6", "Arena Play")],
        ))
        self.assertEqual(games[0]["opponent"], "ЛЕГЕНДА-СТАРТ")
        self.assertIsNone(games[0]["score"])
        self.assertEqual(games[1]["score"], "1 : 2")
        self.assertEqual(games[2]["score"], "6 : 3")
        self.assertEqual(games[2]["result"], "win")

    def test_selects_nearest_future_and_keeps_video_links(self):
        existing = {
            "nextGame": {"date": "17.10.2026", "dateISO": "2026-10-17", "time": "21:45", "arena": "old", "opponent": "old", "tournament": "old"},
            "results": [{"date": "11.10.2026", "dateISO": "2026-10-11", "opponent": "Grizzly team", "score": "0 : 0", "result": "scheduled", "videoUrl": "https://video.example/game"}],
        }
        games = parse_games(page(
            [row("24/10/2026", "20:15", "Лёд", "Arena Play", "", "Поздний соперник"),
             row("17/10/2026", "21:45", "АПИА АРЕНА-2", "Arena Play", "", "ЛЕГЕНДА-СТАРТ")],
            [row("11/10/2026", "18:15", "Созвездие", "Arena Play", "1:2", "Grizzly team")],
        ))
        updated = update_schedule(existing, games, datetime(2026, 10, 13, 7, tzinfo=MOSCOW))
        self.assertEqual(updated["nextGame"]["opponent"], "ЛЕГЕНДА-СТАРТ")
        self.assertEqual(updated["results"][0]["score"], "0 : 0")
        self.assertEqual(updated["results"][1]["score"], "1 : 2")
        self.assertEqual(updated["results"][1]["videoUrl"], "https://video.example/game")

    def test_published_result_replaces_scheduled_zero_zero(self):
        existing = {
            "nextGame": {"date": "11.10.2026", "dateISO": "2026-10-11", "time": "18:15", "arena": "Созвездие", "opponent": "Grizzly team", "tournament": "ДЕБЮТАНТ"},
            "results": [{"date": "11.10.2026", "dateISO": "2026-10-11", "opponent": "Grizzly team", "score": "0 : 0", "result": "scheduled", "videoUrl": "https://video.example/game"}],
        }
        games = parse_games(page(
            [row("24/10/2026", "20:15", "Лёд", "Поздний соперник", "", "Arena Play")],
            [row("11/10/2026", "18:15", "Созвездие", "Arena Play", "1:2", "Grizzly team")],
        ))
        updated = update_schedule(existing, games, datetime(2026, 10, 18, 7, tzinfo=MOSCOW))
        completed = next(game for game in updated["results"] if game["opponent"] == "Grizzly team")
        self.assertEqual(completed["score"], "1 : 2")
        self.assertEqual(completed["result"], "loss")
        self.assertEqual(completed["videoUrl"], "https://video.example/game")

    def test_lhl_zero_zero_in_upcoming_table_stays_scheduled(self):
        current = {
            "nextGame": {"date": "17.10.2026", "dateISO": "2026-10-17", "time": "21:45", "arena": "old", "opponent": "old", "tournament": "old"},
            "results": [],
        }
        games = parse_games(page([
            row("17/10/2026", "21:45", "АПИА АРЕНА-2", "Arena Play", "0:0", "ЛЕГЕНДА-СТАРТ")
        ]))
        updated = update_schedule(current, games, datetime(2026, 10, 13, 7, tzinfo=MOSCOW))
        self.assertEqual(updated["results"][0]["score"], "0 : 0")
        self.assertEqual(updated["results"][0]["result"], "scheduled")

    def test_parser_handles_lhl_rows_with_implicit_tr_closures(self):
        first = row("17/10/2026", "21:45", "АПИА АРЕНА-2", "Arena Play", "0:0", "ЛЕГЕНДА-СТАРТ").replace("</tr>", "")
        second = row("24/10/2026", "20:15", "Лёд", "Arena Play", "0:0", "Соперник").replace("</tr>", "")
        games = parse_games(page([first, second]))
        self.assertEqual([game["opponent"] for game in games], ["ЛЕГЕНДА-СТАРТ", "Соперник"])

    def test_empty_upcoming_section_preserves_last_known_next_game(self):
        existing = {"nextGame": {"dateISO": "2026-10-17", "opponent": "ЛЕГЕНДА-СТАРТ"}, "results": []}
        updated = update_schedule(existing, [], datetime(2026, 10, 13, 7, tzinfo=MOSCOW))
        self.assertEqual(updated["nextGame"], existing["nextGame"])


if __name__ == "__main__":
    unittest.main()
