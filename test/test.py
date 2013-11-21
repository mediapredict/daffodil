import os
import json
import unittest

from daffodil import Daffodil


def load_test_data(dataset):
    filename = os.path.join(os.path.dirname(__file__), 'data', '{0}.json'.format(dataset))
    return json.load(open(filename))

def load_nyc_opendata(dataset):
    dataset = load_test_data(dataset)
    columns = [c['fieldName'] for c in dataset['meta']['view']['columns']]
    d = [dict(zip(columns, row_values)) for row_values in dataset['data']]


class SATDataTests(unittest.TestCase):

    def setUp(self):
        self.d = load_test_data('nyc_sat_scores')

    def filter(self, daff_src):
        return Daffodil(daff_src)(self.d)
    
    def assert_filter_has_n_results(self, n, daff_src):
        self.assertEqual(len(self.filter(daff_src)), n)

    def test_no_filters(self):
        self.assertEqual(len(self.d), 421)
        
    def test_eq(self):
        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers = 50
        """)
    
    def test_ne(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != 50
        """)
        
    def test_gt(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50
        """)
    
    def test_gte(self):
        self.assert_filter_has_n_results(277, """
            num_of_sat_test_takers >= 50
        """)
    
    def test_lt(self):
        self.assert_filter_has_n_results(144, """
            num_of_sat_test_takers < 50
        """)
        
    def test_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50
        """)
    
    def test_multiple(self):
        self.assert_filter_has_n_results(3, """
            num_of_sat_test_takers = 10
            sat_writing_avg_score < 400
            sat_math_avg_score > 200
            sat_critical_reading_avg_score <= 500
        """)
    
    def test_multiple_for_same_value(self):
        self.assert_filter_has_n_results(51, """
            sat_writing_avg_score >= 300
            sat_writing_avg_score < 350
        """)
    
    def test_or(self):
        self.assert_filter_has_n_results(8, """
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)
    
    def test_and_nested_within_or(self):
        self.assert_filter_has_n_results(134, """
            [
                {
                sat_writing_avg_score >= 300
                sat_writing_avg_score < 350
                }
                {
                sat_writing_avg_score >= 400
                sat_writing_avg_score < 450
                }
            ]
        """)
    
    def test_or_mixed_with_literal(self):
        self.assert_filter_has_n_results(11, """
            sat_writing_avg_score < 450
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
                num_of_sat_test_takers = 13
                num_of_sat_test_takers = 14
                num_of_sat_test_takers = 15
            ]
        """)
    
    def test_and_mixed_with_or(self):
        self.assert_filter_has_n_results(6, """
            {
                sat_writing_avg_score > 350
                sat_writing_avg_score < 500
            }
            [
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)
    
    def test_single_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != 50
        """)
    
    def test_double_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            "num_of_sat_test_takers" != 50
        """)
    
    def test_string_eq(self):
        self.assert_filter_has_n_results(1, """
            school_name = "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(1, """
            school_name = 'EAST SIDE COMMUNITY SCHOOL'
        """)
    
    def test_string_ne(self):
        results = self.filter("""
            school_name != "EAST SIDE COMMUNITY SCHOOL"
        """)
        result_dbns = set(r['dbn'] for r in results)
        not_filtered = [dp for dp in self.d 
                        if dp['dbn'] not in result_dbns]
        print not_filtered
        
        self.assert_filter_has_n_results(420, """
            school_name != "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(420, """
            school_name != 'EAST SIDE COMMUNITY SCHOOL'
        """)

if __name__ == "__main__":
    unittest.main()
