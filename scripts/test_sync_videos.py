import json
import unittest

from sync_videos import VIDEO_CATALOG, attach_videos, find_video, parse_videos, parse_rutube_videos


class VideoSyncTests(unittest.TestCase):
    def test_rutube_broadcast_is_matched_and_preferred_over_vk(self):
        url = "https://rutube.ru/video/49ced94394f1c3e9d90af63c5099d7fc/"
        item = {"author": {"id": 35268475}, "title": "Arena Play - Линкор",
                "video_url": url, "publication_ts": "2026-10-22T23:02:30"}
        videos = parse_rutube_videos({"results": [item]})
        game = {"dateISO": "2026-10-24", "opponent": "Линкор"}
        vk = dict(videos[0], url="https://vkvideo.ru/live-71330880_456246354")
        self.assertEqual(find_video(game, [vk, *videos]), url)
        schedule = {"nextGame": dict(game), "results": [dict(game)], "allMatches": [dict(game)]}
        attach_videos(schedule, videos)
        for match in [schedule["nextGame"], *schedule["results"], *schedule["allMatches"]]:
            self.assertEqual(match["videoUrl"], url)

    def test_rutube_rejects_foreign_deleted_and_invalid_videos(self):
        item = {"author": {"id": 35268475}, "title": "Arena Play - Линкор",
                "video_url": "https://rutube.ru/video/49ced94394f1c3e9d90af63c5099d7fc/"}
        self.assertEqual(parse_rutube_videos({"results": [
            dict(item, author={"id": 1}), dict(item, is_deleted=True),
            dict(item, is_hidden=True), dict(item, video_url="https://example.com/")]}), [])

    def test_video_is_attached_to_qualification_in_full_archive(self):
        qualification = {"dateISO": "2026-09-12", "opponent": "ФедКо"}
        upcoming = {"dateISO": "2026-10-24", "opponent": "Линкор"}
        schedule = {"nextGame": upcoming, "results": [], "allMatches": [qualification, dict(upcoming)]}
        url = "https://vkvideo.ru/video-71330880_123"
        attach_videos(schedule, [{"title": "ФедКо — Arena Play", "date": "2026-09-12", "url": url}])
        self.assertEqual(qualification["videoUrl"], url)
        attach_videos(schedule, [])
        self.assertEqual(qualification["videoUrl"], url)

    def test_catalog_metadata_and_matching_reversed_teams(self):
        page = '<script type="application/ld+json">' + json.dumps({
            "@type": "VideoGallery", "video": [{"@type": "VideoObject",
            "name": "Grizzly team — Arena Play", "datePublished": "2026-10-11T18:00:00+03:00",
            "contentUrl": "https://vkvideo.ru/live-71330880_456246255"}]}) + '</script>'
        videos = parse_videos(page)
        self.assertEqual(find_video({"dateISO": "2026-10-11", "opponent": "Grizzly team"}, videos), videos[0]["url"])

    def test_old_match_and_highlights_are_not_future_broadcast(self):
        game = {"dateISO": "2026-10-17", "opponent": "Grizzly team"}
        videos = [{"title": "Arena Play - Grizzly team", "date": "2026-10-11", "url": "old"},
                  {"title": "Хайлайты Arena Play - Grizzly team", "date": "2026-10-17", "url": "highlights"}]
        self.assertIsNone(find_video(game, videos))

    def test_fallback_is_replaced_and_manual_recordings_preserved(self):
        upcoming = {"dateISO": "2026-10-17", "opponent": "Легенда-Старт"}
        scheduled = dict(upcoming, videoUrl=VIDEO_CATALOG)
        old = {"dateISO": "2026-10-11", "opponent": "Grizzly team", "videoUrl": "manual"}
        schedule = {"nextGame": upcoming, "results": [scheduled, old]}
        attach_videos(schedule, [])
        self.assertEqual(upcoming["videoUrl"], VIDEO_CATALOG)
        url = "https://vkvideo.ru/live-71330880_123"
        attach_videos(schedule, [{"title": "Arena Play - Легенда-Старт", "date": "2026-10-16", "url": url}])
        self.assertEqual(upcoming["videoUrl"], url)
        self.assertEqual(scheduled["videoUrl"], url)
        self.assertEqual(old["videoUrl"], "manual")


if __name__ == "__main__":
    unittest.main()
