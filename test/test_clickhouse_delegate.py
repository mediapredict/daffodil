import unittest
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
BUILD = os.path.join(ROOT, 'build', 'lib.linux-x86_64-cpython-312')
sys.path.insert(0, BUILD)
sys.path.insert(0, ROOT)

from daffodil import Daffodil, ClickHouseQueryDelegate

class ClickHouseDelegateTests(unittest.TestCase):
    def _render(self, fltr):
        delegate = ClickHouseQueryDelegate('data')
        return Daffodil(fltr, delegate=delegate)()

    def test_simple(self):
        sql = self._render('zip_code = 8002')
        self.assertEqual(sql, "(data['zip_code'] = 8002)")

    def test_medium(self):
        fltr = '[ gender = "female"\n  gender = "male" ]'
        expected = "((data['gender'] = 'female') OR (data['gender'] = 'male'))"
        self.assertEqual(self._render(fltr), expected)

    def test_advanced(self):
        fltr = '{\n  gender ?= true\n  sat_math_avg_score >= 500\n  ![\n    zip_code = 10001\n    zip_code = 10002\n  ]\n}'
        expected = "((has(data, 'gender')) AND (data['sat_math_avg_score'] >= 500) AND (NOT ((data['zip_code'] = 10001) OR (data['zip_code'] = 10002))))"
        self.assertEqual(self._render(fltr), expected)

    def test_timestamp(self):
        sql = self._render('created >= timestamp(2017-06-01)')
        self.assertEqual(sql, "(data['created'] >= 1496275200.0)")

    def test_in_operators(self):
        sql = self._render('num_of_sat_test_takers in (50, 60)')
        self.assertEqual(sql, "(data['num_of_sat_test_takers'] IN (50, 60))")
        sql = self._render('num_of_sat_test_takers !in (50)')
        self.assertEqual(sql, "(data['num_of_sat_test_takers'] NOT IN (50))")

if __name__ == '__main__':
    unittest.main()
