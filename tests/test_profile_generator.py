from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_live_profile as profile  # noqa: E402


class ProfileGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 11, 18, 16, 40, tzinfo=timezone.utc).astimezone(profile.TEHRAN)

    def test_rial_to_toman_conversion(self) -> None:
        self.assertEqual(profile.fmt_toman(245_288_555), "24,528,856")
        self.assertEqual(profile.fmt_toman(None), "—")
        self.assertEqual(profile.fmt_toman(0), "—")

    def test_timestamp_parsing_handles_z_and_missing_values(self) -> None:
        parsed = profile.parse_timestamp("2026-11-18T16:05:22Z")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.utcoffset().total_seconds(), 12_600)
        self.assertIsNone(profile.parse_timestamp("not-a-date"))
        self.assertIsNone(profile.parse_timestamp(None))

    def test_fresh_market_snapshot(self) -> None:
        market = {
            "timestamp": "2026-11-18T16:39:00Z",
            "lastGoodTimestamp": "2026-11-18T16:39:00Z",
            "gold18K": 245_288_555,
            "usdtPrice": 2_704_500,
            "derivedStale": {"gold18K": False, "dollar": False},
            "prices": {
                "USDT": {"lastPrice": 2_704_500, "stale": False, "source": "Nobitex"},
                "XAUT": {"lastPrice": 3_761.3, "stale": False},
            },
        }
        snapshot = profile.market_snapshot(market, self.now)
        self.assertEqual(snapshot["gold"], "24,528,856")
        self.assertTrue(snapshot["gold_fresh"])
        self.assertTrue(snapshot["dollar_fresh"])
        self.assertEqual(snapshot["usdt"], "270,450")

    def test_stale_sensor_is_not_marked_online(self) -> None:
        status = {
            "nodes": {
                "esp32_1": {
                    "name": "Room 1 · Hub", "online": True, "temperature": 24.2,
                    "humidity": 42.0, "last_seen": "2026-11-18T15:00:00Z",
                }
            }
        }
        node = profile.sensor_snapshot(status, "esp32_1", self.now)
        self.assertEqual(node["state"], "STALE")
        self.assertFalse(node["fresh"])

    def test_only_personal_rating_is_treated_as_personal(self) -> None:
        self.assertEqual(profile.movie_rating({"user_rating": 9.2, "imdb_rating": "7.8"}), 9.2)
        self.assertEqual(profile.movie_rating({"rating": 9.9, "imdb_rating": "8.1"}), 0.0)

    def test_svg_renderer_produces_well_formed_markup(self) -> None:
        market = {
            "timestamp": "2026-11-18T16:39:00Z", "lastGoodTimestamp": "2026-11-18T16:39:00Z",
            "gold18K": 245_288_555, "usdtPrice": 2_704_500,
            "derivedStale": {"gold18K": False, "dollar": False},
            "prices": {"USDT": {"lastPrice": 2_704_500, "stale": False}, "XAUT": {"stale": False}},
        }
        status = {
            "generated_at": "2026-11-18T19:39:00+03:30",
            "nodes": {
                "esp32_1": {"name": "Room 1 Hub", "online": True, "temperature": 23.9, "humidity": 41.0,
                            "last_seen": "2026-11-18T19:39:00+03:30", "latency_ms": 42, "samples": 10},
                "esp32_s3": {"name": "Room 2 S3", "online": False, "temperature": 27.9, "humidity": 30.7,
                             "last_seen": "2026-11-18T19:39:00+03:30", "latency_ms": 80, "samples": 9},
            },
        }
        svg = profile.render_live_dashboard(market, status, self.now)
        root = ET.fromstring(svg)
        self.assertEqual(root.tag.split("}")[-1], "svg")
        self.assertIn("24,528,856", svg)
        self.assertIn("23.9", svg)
        self.assertIn("OFFLINE", svg)


if __name__ == "__main__":
    unittest.main()
