import unittest
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)

from daffodil import Daffodil
from daffodil.clickhouse_query_delegate import ClickHouseQueryDelegate

class ClickHouseDelegateTests(unittest.TestCase):
    def _render(self, fltr):
        delegate = ClickHouseQueryDelegate()
        return Daffodil(fltr, delegate=delegate)()

    def test_simple(self):
        sql = self._render('zip_code = 8002')
        self.assertEqual(sql, "(hs_data.zip_code = 8002)")

    def test_medium(self):
        fltr = '[ gender = "female"\n  gender = "male" ]'
        expected = "((hs_data.gender = 'female') OR (hs_data.gender = 'male'))"
        self.assertEqual(self._render(fltr), expected)

    def test_advanced(self):
        fltr = '{\n  gender ?= true\n  sat_math_avg_score >= 500\n  ![\n    zip_code = 10001\n    zip_code = 10002\n  ]\n}'
        expected = "((isNotNull(hs_data.gender)) AND (hs_data.sat_math_avg_score >= 500) AND (NOT ((hs_data.zip_code = 10001) OR (hs_data.zip_code = 10002))))"
        self.assertEqual(self._render(fltr), expected)

    def test_timestamp(self):
        sql = self._render('created >= timestamp(2017-06-01)')
        self.assertEqual(sql, "(hs_data.created >= 1496275200.0)")

    def test_in_operators(self):
        sql = self._render('num_of_sat_test_takers in (50, 60)')
        self.assertEqual(sql, "(hs_data.num_of_sat_test_takers IN (50, 60))")
        sql = self._render('num_of_sat_test_takers !in (50)')
        self.assertEqual(sql, "(hs_data.num_of_sat_test_takers NOT IN (50))")

    def test_existence_false(self):
        sql = self._render('zip_code ?= false')
        self.assertEqual(sql, "(isNull(hs_data.zip_code))")

if __name__ == '__main__':
    unittest.main()
