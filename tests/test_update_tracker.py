import json
import unittest
from pathlib import Path
from unittest import mock

from scripts.update_tracker import build_market_data, update_html

FIXTURE_CSV = """RegionID,SizeRank,RegionName,RegionType,StateName,State,Metro,CountyName,2026-01-31,2026-02-28,2026-03-31
1,1,San Mateo,city,California,CA,San Francisco,San Mateo County,1671944,1680716,1686905
2,2,Albany,city,California,CA,San Francisco,Alameda County,1256043,1260334,1261177
3,3,Oakland,city,California,CA,San Francisco,Alameda County,800000,801000,802000
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<body>
  <span id='last-update'>2026-02</span>
  <script>
    const AREA_DATA = {"san-mateo": {"medianSqft": 1650, "pricePerSqft": 970, "basePrice": 1638485}, "albany": {"medianSqft": 1450, "pricePerSqft": 815, "basePrice": 1224400}};
    const HISTORY = {"san-mateo": [{"date": "2026-02", "price": 1638485}], "albany": [{"date": "2026-02", "price": 1224400}]};
    var lastDataDate = new Date('2026-02-28');
  </script>
</body>
</html>
"""


class BuildMarketDataTests(unittest.TestCase):
    def test_build_market_data_extracts_latest_month_and_history(self):
        data = build_market_data(FIXTURE_CSV)

        self.assertEqual(data["latest_month"], "2026-03")
        self.assertEqual(data["last_data_date"], "2026-03-31")
        self.assertEqual(data["area_data"]["san-mateo"]["basePrice"], 1686905)
        self.assertEqual(data["history"]["albany"][-1], {"date": "2026-03", "price": 1261177})
        self.assertEqual(len(data["history"]["san-mateo"]), 3)


class UpdateHtmlTests(unittest.TestCase):
    def test_update_html_replaces_embedded_tracker_data(self):
        market_data = build_market_data(FIXTURE_CSV)

        updated = update_html(HTML_TEMPLATE, market_data)

        self.assertIn("<span id='last-update'>2026-03</span>", updated)
        self.assertIn('1686905', updated)
        self.assertIn('1261177', updated)
        self.assertIn("var lastDataDate = new Date('2026-03-31');", updated)
        self.assertEqual(updated.count("const AREA_DATA ="), 1)
        self.assertEqual(updated.count("const HISTORY ="), 1)


if __name__ == '__main__':
    unittest.main()
