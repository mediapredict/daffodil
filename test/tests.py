from builtins import zip
import sys
import os
import json
import unittest
import re
import itertools


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from daffodil import (
    Daffodil,
    KeyExpectationDelegate, DictionaryPredicateDelegate,
    HStoreQueryDelegate, PrettyPrintDelegate, SimulationMatchingDelegate
)
from daffodil.exceptions import ParseError


def load_test_data(dataset):
    filename = os.path.join(os.path.dirname(__file__), 'data', '{0}.json'.format(dataset))
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def load_nyc_opendata(dataset):
    dataset = load_test_data(dataset)
    columns = [c['fieldName'] for c in dataset['meta']['view']['columns']]
    d = [dict(list(zip(columns, row_values))) for row_values in dataset['data']]


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.d = load_test_data('nyc_sat_scores')

    def filter(self, daff_src):
        return Daffodil(daff_src)(self.d)


class ParserGrammarTypesTests(unittest.TestCase):
    def parse(self, daff_src, delegate):
        return Daffodil(daff_src, delegate=delegate)

    def test_existence_doesnt_expect_string(self):
        for delegate in [
            HStoreQueryDelegate(hstore_field_name="dummy_name"),
            DictionaryPredicateDelegate(), KeyExpectationDelegate()
        ]:
            with self.assertRaises(ValueError):
                self.parse('whatever ?= "true"', delegate)
            with self.assertRaises(ValueError):
                self.parse('whatever ?= "False"', delegate)
            with self.assertRaises(ValueError):
                self.parse('whatever ?= "any string"', delegate)
            with self.assertRaises(ParseError):
                self.parse('whatever >= timestamp(2017-13-10)', delegate)
            with self.assertRaises(ParseError):
                self.parse('whatever in (timestamp(2017-11-21 21:99), timestamp(2021-11-21 14:30))', delegate)

    def test_dirty_strings_parsed(self):
        #
        # string containing '7\n\ufeff208' substring
        # (end of 1st and beginning of the 2nd line)
        #
        dirty_string = """(
            2082237
            ﻿2082261
            ﻿2082360)
        """
        for delegate in [
            HStoreQueryDelegate(hstore_field_name="dummy_name"),
            DictionaryPredicateDelegate(), KeyExpectationDelegate()
        ]:
            self.parse(f"whatever in {dirty_string}", delegate)


class SATDataTests(BaseTest):
    def assert_filter_has_n_results(self, n, daff_src):
        self.assertEqual(len(self.filter(daff_src)), n)

    def test_no_filters(self):
        self.assertEqual(len(self.d), 421)

    def test_empty(self):
        self.assert_filter_has_n_results(421, "")
        self.assert_filter_has_n_results(421, "{}")
        self.assert_filter_has_n_results(421, "{ }")
        self.assert_filter_has_n_results(421, "{\n}")

        self.assert_filter_has_n_results(0, "[]")
        self.assert_filter_has_n_results(0, "[ ]")
        self.assert_filter_has_n_results(0, "[\n]")

        self.assert_filter_has_n_results(0, "!{}")
        self.assert_filter_has_n_results(0, "!{ }")
        self.assert_filter_has_n_results(0, "!{\n}")

        self.assert_filter_has_n_results(421, "![]")
        self.assert_filter_has_n_results(421, "![ ]")
        self.assert_filter_has_n_results(421, "![\n]")

    def test_none(self):
        self.d = [None]
        self.assert_filter_has_n_results(1, """
            num_of_sat_test_takers != 50
        """)
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers = 50
        """)
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers ?= True
        """)
        self.assert_filter_has_n_results(1, """
            num_of_sat_test_takers ?= False
        """)

    def test_int_eq(self):
        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers = 50
        """)

    def test_int_in_list(self):
        self.assert_filter_has_n_results(8, """
            num_of_sat_test_takers in (10, 11, 12)
        """)

    def test_int_in_list_multiline(self):
        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers in
            (
            50
            )
        """)

    def test_int_ne(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != 50
        """)

    def test_int_not_in_list(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers !in (50)
        """)

    def test_int_not_in_list_multiline(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers !in
            (
            50
            )
        """)

    def test_int_gt(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50
        """)

    def test_int_gte(self):
        self.assert_filter_has_n_results(277, """
            num_of_sat_test_takers >= 50
        """)

    def test_int_lt(self):
        self.assert_filter_has_n_results(144, """
            num_of_sat_test_takers < 50
        """)

    def test_non_existing_tag_lt_gt(self):
        self.assert_filter_has_n_results(0, """
            tag_with_null_value < 1236
        """)
        self.assert_filter_has_n_results(0, """
            tag_with_null_value >= 1236
        """)
        self.assert_filter_has_n_results(0, """
            tag_with_null_value = 1236
        """)
        # doesn't break the "sane part" of evaluation
        self.assert_filter_has_n_results(4, """
            [
                tag_with_null_value >= 1236
                num_of_sat_test_takers = 50
            ]
        """)

    def test_int_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50
        """)

    def test_int_zero_leading_as_a_string(self):
        self.assert_filter_has_n_results(1, """
            zip_code = 8002
        """)
        self.assert_filter_has_n_results(3, """
            zip_code in (8002, 8003, 10004)
        """)
        self.assert_filter_has_n_results(2, """
            {
                zip_code > 8001
                zip_code < 8004
            }
        """)

    def test_float_eq(self):
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers = 50.5
        """)

    def test_float_str_eq(self):
        self.assert_filter_has_n_results(2, """
            total_score = 1120.0
        """)
        self.assert_filter_has_n_results(2, """
            total_score = "1120.0"
        """)
        self.assert_filter_has_n_results(0, """
            total_score = "1120"
        """)
        self.assert_filter_has_n_results(2, """
            total_score = 1120
        """)

        # now inside an array
        self.assert_filter_has_n_results(2, """
            total_score in (1120.0)
        """)
        self.assert_filter_has_n_results(2, """
            total_score in ("1120.0")
        """)
        self.assert_filter_has_n_results(0, """
            total_score in ("1120")
        """)
        self.assert_filter_has_n_results(2, """
            total_score in (1120)
        """)

    def test_float_ne(self):
        self.assert_filter_has_n_results(421, """
            num_of_sat_test_takers != 50.5
        """)

    def test_float_gt(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50.5
        """)

    def test_float_gte(self):
        self.assert_filter_has_n_results(277, """
            num_of_sat_test_takers >= 50.0
        """)

    def test_float_lt(self):
        self.assert_filter_has_n_results(144, """
            num_of_sat_test_takers < 49.5
        """)

    def test_float_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50.0
        """)

    def test_multiple(self):
        self.assert_filter_has_n_results(3, """
            num_of_sat_test_takers = 10
            sat_writing_avg_score < 400
            sat_math_avg_score > 200
            sat_critical_reading_avg_score <= 500
        """)
        self.assert_filter_has_n_results(3, """
            num_of_sat_test_takers ?= true
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

    def test_not_or(self):
        self.assert_filter_has_n_results(413, """
            ![
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)

    def test_and(self):
        self.assert_filter_has_n_results(51, """
            {
                sat_writing_avg_score >= 300
                sat_writing_avg_score < 350
            }
        """)

    def test_not_and(self):
        self.assert_filter_has_n_results(370, """
            !{
                sat_writing_avg_score >= 300
                sat_writing_avg_score < 350
            }
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

    def test_not_and_nested_within_or(self):
        self.assert_filter_has_n_results(370, """
            [
                !{
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

    def test_not_or_mixed_with_literal(self):
        self.assert_filter_has_n_results(4, """
            sat_writing_avg_score < 300
            ![
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
                num_of_sat_test_takers = 13
                num_of_sat_test_takers = 14
                num_of_sat_test_takers = 15
            ]
        """)

    def test_in_mixed_with_literal(self):
        self.assert_filter_has_n_results(11, """
            sat_writing_avg_score < 450
            num_of_sat_test_takers in (
                10, 11
                12, 13, 14,
                15
            )
        """)

    def test_not_in_mixed_with_literal(self):
        self.assert_filter_has_n_results(4, """
            sat_writing_avg_score < 300
            num_of_sat_test_takers !in (
                10, 11
                12, 13, 14,
                15
            )
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
        self.assert_filter_has_n_results(6, """
            sat_writing_avg_score ?= true
            sat_writing_avg_score > 350
            sat_writing_avg_score < 500
            [
                asdf ?= true
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)
        self.assert_filter_has_n_results(338, """
            sat_writing_avg_score > 350
            sat_writing_avg_score < 500
            [
                sat_writing_avg_score ?= true
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)

    def test_not_and_mixed_with_not_or(self):
        self.assert_filter_has_n_results(81, """
            !{
                sat_writing_avg_score > 350
                sat_writing_avg_score < 500
            }
            ![
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)

    def test_single_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != 50
        """)
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != '50'
        """)
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' !in ('50')
        """)

    def test_double_quoted_fields(self):
        self.assert_filter_has_n_results(417, """
            "num_of_sat_test_takers" != 50
        """)
        self.assert_filter_has_n_results(417, """
            "num_of_sat_test_takers" != "50"
        """)

    def test_string_eq(self):
        self.assert_filter_has_n_results(1, """
            school_name = "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(1, """
            school_name = 'EAST SIDE COMMUNITY SCHOOL'
        """)

    def test_string_containing_special_chars(self):
        self.assert_filter_has_n_results(0, """
            not_existing_param = 'this "word" is within double quotes'
        """)
        self.assert_filter_has_n_results(0, """
            not_existing_param = "we have a back tick ` in this sentence"
        """)
        self.assert_filter_has_n_results(0, """
            some_non_existing_period > "60'"
        """)
        self.assert_filter_has_n_results(421, """
            some_non_existing_period != "60'"
        """)
        self.assert_filter_has_n_results(0, """
            some_non_existing_minutes = '60"'
        """)
        self.assert_filter_has_n_results(0, """
            not_existing_param = "goin' word contains single quote"
        """)

    def test_string_within_array_containing_special_chars(self):
        self.assert_filter_has_n_results(0, """
            some_non_existing_period in ("50'", "60'")
        """)
        self.assert_filter_has_n_results(0, """
            some_non_existing_minutes in ('50"', '60"')
        """)
        self.assert_filter_has_n_results(0, """
            some_non_existing_quoted_param in ('"x"', '"y"')
        """)

    def test_string_ne(self):
        self.assert_filter_has_n_results(420, """
            school_name != "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(420, """
            school_name != 'EAST SIDE COMMUNITY SCHOOL'
        """)

    def test_timestamp_eq(self):
        self.assert_filter_has_n_results(1, """
            created = timestamp(2017-11-21 16:27)
        """)
        self.assert_filter_has_n_results(0, """
            created = timestamp(2017-11-21)
        """)

    def test_timestamp_ne(self):
        self.assert_filter_has_n_results(420, """
            created != timestamp(2017-11-21 16:27)
        """)
        self.assert_filter_has_n_results(421, """
            created != timestamp(2017-06-01)
        """)

    def test_timestamp_gt(self):
        self.assert_filter_has_n_results(2, """
            created > timestamp(2017-06-01)
        """)
        self.assert_filter_has_n_results(0, """
            created > timestamp(2017-11-21 16:27)
        """)

    def test_timestamp_gte(self):
        self.assert_filter_has_n_results(2, """
            created >= timestamp(2017-06-01)
        """)
        self.assert_filter_has_n_results(1, """
            created >= timestamp(2017-11-21 16:27)
        """)

    def test_timestamp_lt(self):
        self.assert_filter_has_n_results(2, """
            created < timestamp(2017-06-01)
        """)
        self.assert_filter_has_n_results(3, """
            created < timestamp(2017-11-21 16:27)
        """)

    def test_timestamp_lte(self):
        self.assert_filter_has_n_results(2, """
            created <= timestamp(2017-06-01)
        """)
        self.assert_filter_has_n_results(4, """
            created <= timestamp(2017-11-21 16:27)
        """)

    def test_timestamp_in(self):
        self.assert_filter_has_n_results(1, """
            created in (
                timestamp(2017-06-01)
                timestamp(2017-11-21 16:27)
            )
        """)

    def test_timestamp_notin(self):
        self.assert_filter_has_n_results(420, """
            created !in (
                timestamp(2017-06-01)
                timestamp(2017-11-21 16:27)
            )
        """)


    #def test_comparing_a_string_containing_int(self):
    #    self.assert_filter_has_n_results(417, """
    #        num_of_sat_test_takers != "50"
    #    """)

    #def test_comparing_a_string_containing_float(self):
    #    self.assert_filter_has_n_results(417, """
    #        num_of_sat_test_takers != "50.0"
    #    """)

    def test_missing_field(self):
        self.assert_filter_has_n_results(0, """
            numOfSatTestTakers-9-17-2013 = 99
        """)
        self.assert_filter_has_n_results(421, """
            numOfSatTestTakers_9-17-2013 != 99
        """)
        self.assert_filter_has_n_results(0, """
            "number of SAT Test Takers 9-17-2013" = 99
        """)
        self.assert_filter_has_n_results(421, """
            "number of SAT Test Takers 9-17-2013" != 99
        """)

    def test_invalid_filter(self):
        self.assertRaises(ParseError, Daffodil, """
            [
        """)
        self.assertRaises(ParseError, Daffodil, """
            {
              a = 1
              b = 2
            } {
              x = 3
              y = 4
            }
        """)
        self.assertRaises(ParseError, Daffodil, """
            [
              a = 1
              b = 2
            ] [
              c = 3
              d = 4
            ]
        """)
        self.assertRaises(ParseError, Daffodil, "a = 1 }")
        self.assertRaises(ParseError, Daffodil, "a = 1 ]")
        self.assertRaises(ParseError, Daffodil, "a = 1 \n}")
        self.assertRaises(ParseError, Daffodil, "a = 1 \n]")

        self.assertRaises(ValueError, Daffodil, "a = 'bcd\\'")

    def test_unicode_filter(self):
        self.assert_filter_has_n_results(273, """
            num_of_sat_test_takers > 50
        """)

    def test_existance_has_value(self):
        self.assert_filter_has_n_results(421, """
            num_of_sat_test_takers ?= true
        """)
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers ?= false
        """)
        self.assert_filter_has_n_results(421, """
            "num_of_sat_test_takers" ?= true
        """)
        self.assert_filter_has_n_results(0, """
            "num_of_sat_test_takers" ?= false
        """)
        self.assert_filter_has_n_results(421, """
            'num_of_sat_test_takers' ?= true
        """)
        self.assert_filter_has_n_results(0, """
            'num_of_sat_test_takers' ?= false
        """)

    def test_existance_does_not_have_value(self):
        self.assert_filter_has_n_results(0, """
            asdf ?= true
        """)
        self.assert_filter_has_n_results(421, """
            asdf ?= false
        """)
        self.assert_filter_has_n_results(0, """
            "asdf" ?= true
        """)
        self.assert_filter_has_n_results(421, """
            "asdf" ?= false
        """)
        self.assert_filter_has_n_results(0, """
            'asdf' ?= true
        """)
        self.assert_filter_has_n_results(421, """
            'asdf' ?= false
        """)

    def test_existance_multiple(self):
        self.assert_filter_has_n_results(421, """
            [
                total_score ?= true
                num_of_sat_test_takers ?= true
            ]
        """)
        self.assert_filter_has_n_results(421, """
            [
                total_score ?= false
                num_of_sat_test_takers ?= true
            ]
        """)
        self.assert_filter_has_n_results(0, """
            {
                total_score ?= false
                num_of_sat_test_takers ?= false
            }
        """)
        self.assert_filter_has_n_results(4, """
            {
                total_score ?= true
                num_of_sat_test_takers ?= true
            }
        """)
        self.assert_filter_has_n_results(417, """
            {
                total_score ?= false
                num_of_sat_test_takers ?= true
            }
        """)

    def test_comparing_string_data_to_an_int_filter(self):
        self.assert_filter_has_n_results(0, """
            dbn = 7
        """)
        self.assert_filter_has_n_results(0, """
            dbn > 7
        """)
        self.assert_filter_has_n_results(421, """
            dbn != 7
        """)
        self.assert_filter_has_n_results(0, """
            dbn = -7
        """)
        self.assert_filter_has_n_results(0, """
            dbn > -7
        """)
        self.assert_filter_has_n_results(421, """
            dbn != -7
        """)

    def test_comparing_string_data_to_a_float_filter(self):
        self.assert_filter_has_n_results(0, """
            dbn = 7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn > 7.5
        """)
        self.assert_filter_has_n_results(421, """
            dbn != 7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn = -7.5
        """)
        self.assert_filter_has_n_results(0, """
            dbn > -7.5
        """)
        self.assert_filter_has_n_results(421, """
            dbn != -7.5
        """)

    def test_comments(self):
        self.assert_filter_has_n_results(4, """
            {{num_of_sat_test_takers = 50,num_of_sat_test_takers = 50}}
        """)

        self.assert_filter_has_n_results(4, """
            # omg1
            num_of_sat_test_takers = 50
            # omg2
            num_of_sat_test_takers = 50 # omg3
            # omg4
        """)

        self.assert_filter_has_n_results(0, """
            {val1 = 10,val2 = 29}
        """)

        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers = 50 # this is inline comment
        """)

        self.assert_filter_has_n_results(3, """
            # this is 1st comment
            num_of_sat_test_takers = 10
            sat_writing_avg_score < 400
            # this is 2nd comment
            sat_math_avg_score > 200
            sat_critical_reading_avg_score <= 500
            # this is 3d comment
        """)

        #
        # or, not or, and, not and
        #

        self.assert_filter_has_n_results(4, """
            [
                # this is a comment
                num_of_sat_test_takers = 50
            ]
        """)
        self.assert_filter_has_n_results(413, """
            ![
                # this is a comment
                num_of_sat_test_takers = 10
                num_of_sat_test_takers = 11
                num_of_sat_test_takers = 12
            ]
        """)
        self.assert_filter_has_n_results(4, """
            # this is 1st comment
            {
                # this is 2nd comment
                num_of_sat_test_takers = 50 # this is 3rd comment
            }
        """)
        self.assert_filter_has_n_results(370, """
            !{
                # this is a comment
                sat_writing_avg_score >= 300
                sat_writing_avg_score < 350
            }
        """)

        # less expected places + bad formatting
        self.assert_filter_has_n_results(4, """
            {# this is 1st comment
            #this is 2nd comment
                num_of_sat_test_takers = 50
                #
                #
                # this is 3d comment
            }

            #
            # and yet 4th comment
            #
        """)

    def test_dollar_sign_in_variable_name(self):
        # with quotes
        self.assert_filter_has_n_results(1, """
            "$calculated_pct" = "85"
        """)
        self.assert_filter_has_n_results(1, """
            '$calculated_pct' ?= true
        """)

        # without quotes
        self.assert_filter_has_n_results(1, """
            $calculated_pct = "85"
        """)


class PredicateTests(unittest.TestCase):
    def setUp(self):
        self.data = {
          "MHQ9ProgsWatched - GoldRush": "no",
          "MHQ9ProgsWatched - PawnStars": "yes",
          "MHQ9ProgsWatched - BornSurvivor": "no",
          "MHQ9ProgsWatched - AirCrashInvestigation": "no",
          "MHQ9ProgsWatched - AmericanPickers": "no",
          "MHQ9ProgsWatched - StorageWars": "yes",
          "MHQ9ProgsWatched - TopGear": "no",
          "MHQ9ProgsWatched - FifthGear": "no",
          "MHQ9ProgsWatched - WheelerDealers": "no",
          "MHQ9ProgsWatched - FastNLoud": "no",
          "MHQ9ProgsWatched - MythBusters": "no",
          "MHQ9ProgsWatched - DeadliestCatch": "no",
          "MHQ9ProgsWatched - WickedTuna": "no",
          "MHQ9ProgsWatched - AuctionHunters": "no",
          "MHQ9ProgsWatched - AmericanChopper": "no",
          "MHQ9ProgsWatched - SonsOfGuns": "no"
        }

    def test_keys(self):
        daff = Daffodil("""
        {
          "k1" = "no"
          [
            k2 = 1.7
            k3 > 5
          ]
          [
            "k4" ?= true
            "k5" = "words"
          ]
        }
        """)
        self.assertEqual(daff.keys, set(["k1", "k2", "k3", "k4", "k5"]))

    def test_matching(self):
        daff = Daffodil("""
        {
           "MHQ9ProgsWatched - BornSurvivor" = "no"
           "MHQ9ProgsWatched - WheelerDealers" = "no"
           "MHQ9ProgsWatched - FifthGear" = "no"
           "MHQ9ProgsWatched - AuctionHunters" = "no"
           "MHQ9ProgsWatched - MythBusters" = "no"
           "MHQ9ProgsWatched - GoldRush" = "no"
           "MHQ9ProgsWatched - DeadliestCatch" = "no"
           "MHQ9ProgsWatched - FastNLoud" = "no"
           "MHQ9ProgsWatched - SonsOfGuns" = "no"
           "MHQ9ProgsWatched - AmericanChopper" = "no"
        }
        """)
        self.assertTrue(daff.predicate(self.data))

        daff = Daffodil("""{
           "MHQ9ProgsWatched - BornSurvivor" = 'no'
           "MHQ9ProgsWatched - WheelerDealers" = 'no'
           "MHQ9ProgsWatched - FifthGear" = 'no'
           "MHQ9ProgsWatched - AuctionHunters" = 'no'
           "MHQ9ProgsWatched - MythBusters" = 'no'
           "MHQ9ProgsWatched - GoldRush" = 'no'
           "MHQ9ProgsWatched - DeadliestCatch" = 'no'
           "MHQ9ProgsWatched - FastNLoud" = 'no'
           "MHQ9ProgsWatched - SonsOfGuns" = 'no'
           "MHQ9ProgsWatched - AmericanChopper" = 'no'
        }""")
        self.assertTrue(daff.predicate({
           'MHQ9ProgsWatched - PawnStars': 'yes', 'MHQ3Gender': 'Female', 'MHQ9ProgsWatched - FastNLoud': 'no', 'MHQ8ChannelViewing - Discovery Channel': 'OncePerWeek', 'MHQ8ChannelViewing - National Geographic': 'OncePerWeek', '_sample_id': 'frutest3', 'MHQ4TVProvider - YouView': 'no', 'MHQ6Industry - MarketResearch': 'no', 'MHQ6Industry - Entertainment': 'no', 'MHQ5TVViewing': '1-3nights', 'MHQ8ChannelViewing - ITV1': 'OncePerWeek', 'MHQ7PastParticipant': 'No', 'MHQ9ProgsWatched - StorageWars': 'yes', 'MHQ8ChannelViewing - History Channel': 'OncePerWeek', 'MHQ8ChannelViewing - BBC2': 'OncePerWeek', 'MHQ1Confidential': 'Yes', 'MHQ4TVProvider - Freeview': 'no', 'MHQ9ProgsWatched - BornSurvivor': 'no', 'MHQ9ProgsWatched - WheelerDealers': 'no', 'MHQ8ChannelViewing - Channel4': 'OncePerWeek', 'MHQ4TVProvider - IPTV': 'no', 'MHQ9ProgsWatched - AuctionHunters': 'no', 'MHQ9ProgsWatched - AirCrashInvestigation': 'no', 'MHQ8ChannelViewing - Sky Arts': 'OncePerWeek', 'MHQ2Age': '18-34', 'MHQ8ChannelViewing - BBC1': 'OncePerWeek', 'MHQ6Industry - None': 'yes', 'MHQ4TVProvider - None': 'no', 'MHQ6Industry - RadioTV': 'no', 'MHQ6Industry - Advertising': 'no', 'MHQ9ProgsWatched - DeadliestCatch': 'no', 'MHQ9ProgsWatched - FifthGear': 'no', 'MHQ9ProgsWatched - TopGear': 'no', 'MHQ9ProgsWatched - SonsOfGuns': 'no', 'MHQ9ProgsWatched - WickedTuna': 'no', 'MHQ9ProgsWatched - GoldRush': 'no', 'MHQ9ProgsWatched - MythBusters': 'no', 'MHQ6Industry - Press': 'no', 'MHQ4TVProvider - Virgin': 'yes', '_id': '41298', 'MHQ9ProgsWatched - AmericanPickers': 'no', 'MHQ9ProgsWatched - AmericanChopper': 'no', 'MHQ4TVProvider - Sky': 'no'
        }))

    def test_not_matching(self):
        daff = Daffodil("""
        {
           "MHQ9ProgsWatched - MythBusters" = "yes"
           "MHQ9ProgsWatched - BornSurvivor" = "no"
           "MHQ9ProgsWatched - WheelerDealers" = "no"
           "MHQ9ProgsWatched - FifthGear" = "no"
           "MHQ9ProgsWatched - AuctionHunters" = "no"
           "MHQ9ProgsWatched - GoldRush" = "no"
           "MHQ9ProgsWatched - DeadliestCatch" = "no"
           "MHQ9ProgsWatched - FastNLoud" = "no"
           "MHQ9ProgsWatched - SonsOfGuns" = "no"
           "MHQ9ProgsWatched - AmericanChopper" = "no"
        }
        """)

        self.assertFalse(daff.predicate(self.data))


class KeyExpectationTests(unittest.TestCase):

    def assert_daffodil_expectations(self, dafltr, present=set(), omitted=set()):
        daff = Daffodil(dafltr, delegate=KeyExpectationDelegate())
        daff_expected_present, daff_expected_omitted = daff.predicate
        self.assertEqual(daff_expected_present, present)
        self.assertEqual(daff_expected_omitted, omitted)

    def test_key_expectations(self):
        self.assert_daffodil_expectations(
            "x = 1, y = true",
            present={"x", "y"}
        )
        self.assert_daffodil_expectations(
            "x ?= true, y ?= false",
            present={"x"}, omitted={"y"}
        )
        self.assert_daffodil_expectations(
            "!{x ?= true, y ?= false}",
            present={"y"}, omitted={"x"}
        )
        self.assert_daffodil_expectations(
            """
                !{
                    [
                        x ?= true
                        y ?= false
                    ]
                    ![
                        z = "a"
                        {
                          a = 1
                          b != 2
                          c > 10
                          d < 9
                        }
                    ]
                }
                a ?= false
            """,
            present={"a", "b", "c", "d", "y", "z"}, omitted={"x"}
        )


class SimulationDelegatesTests(unittest.TestCase):
    def mk_predicate(self, dafltr):
        return Daffodil(dafltr, delegate=SimulationMatchingDelegate()).predicate

    def assertMatch(self, matches, possibility_space, dafltr):
        pred = self.mk_predicate(dafltr)
        self.assertEqual(pred(possibility_space), matches)

    def test_known_matches(self):
        possibility_space = {
            "lang": "en",
            "mp_birth_year": [],
            "mp_gender": ["male", "female"],
            "graduation_year": ["2006", "2007", 2008],
            "irregular_data": ["1", 2, "three", 4.0, None],
            "irregular_single_1": "1",
            "irregular_single_2": 2,
        }

        will_match = [
            "lang ?= true # comment\n",
            "mp_birth_year ?= true\n # comment\n",
            "mp_gender ?= true",
            "fake_key ?= false",
            "lang = 'en'",
            "lang != 'hi'",
            "mp_gender != 'dude'",
            "mp_gender > 'dude'",
            "mp_gender >= 'dude'",
            "mp_gender >= 'female'",
            "mp_gender in ('male', 'dude', 'lady', 'female')",
            "mp_gender !in ('dude', 'lady')",
            "graduation_year ?= true",
            "graduation_year in ('2006', '2007', '2008', '2009')",
            "graduation_year in (2006, 2007, 2008, 2009)",
            "irregular_data ?= true",
            "irregular_data != 'fifty'",
            "irregular_data != (6, 7)",
            "irregular_data != ('8', '9')",
            "irregular_single_1 = 1",
            "irregular_single_1 != 3",
            "irregular_single_2 ?= true",
        ]
        wont_match = [
            "lang ?= false # comment\n",
            "mp_birth_year ?= false\n # comment\n",
            "mp_gender ?= false",
            "fake_key ?= true",
            "lang != 'en'",
            "lang = 'hi'",
            "mp_gender = 'dude'",
            "mp_gender < 'dude'",
            "mp_gender <= 'dude'",
            "mp_gender < 'female'",
            "mp_gender !in ('male', 'dude', 'lady', 'female')",
            "mp_gender in ('dude', 'lady')",
            "graduation_year < 2003",
            "graduation_year < '2003'",
            "irregular_data ?= false",
            "irregular_data = 7",
            "irregular_data = 'eight'",
            "irregular_data in (6, 7)",
            "irregular_single_1 = 'one'",
            "irregular_single_1 = 5",
            "irregular_single_2 ?= false",
        ]
        might_match = [
            "mp_birth_year = '1995' # comment\n",
            "mp_birth_year = '1995'\n # comment\n",
            "mp_birth_year < '1995'",
            "mp_birth_year <= '1995'",
            "mp_birth_year > '1995'",
            "mp_birth_year >= '1995'",
            "mp_birth_year in ('1995', '1996', '1997')",
            "mp_birth_year !in ('1995', '1996', '1997')",
            "mp_gender in ('male', 'dude')",
            "mp_gender !in ('male', 'dude')",
            "graduation_year >= 2007",
            "graduation_year > '2007'",
            "graduation_year = 2007",
            "irregular_data = 1",
            "irregular_data = '1'",
            "irregular_data in (1, 9)",
            "irregular_data in ('three')",
        ]

        for dafltr in will_match:
            self.assertMatch(True, possibility_space, dafltr)

        for dafltr in wont_match:
            self.assertMatch(False, possibility_space, dafltr)

        for dafltr in might_match:
            self.assertMatch(None, possibility_space, dafltr)

        for dafltr_t, dafltr_f in itertools.product(will_match, wont_match):
            self.assertMatch(False, possibility_space, "{}\n{}".format(dafltr_t, dafltr_f))
            self.assertMatch(True, possibility_space, "!{{ {}\n{} }}".format(dafltr_t, dafltr_f))
            self.assertMatch(True, possibility_space, "[{}\n{}]".format(dafltr_t, dafltr_f))
            self.assertMatch(False, possibility_space, "![{}\n{}]".format(dafltr_t, dafltr_f))

        for dafltr_t, dafltr_maybe in itertools.product(will_match, might_match):
            self.assertMatch(None, possibility_space, "{}\n{}".format(dafltr_t, dafltr_maybe))
            self.assertMatch(None, possibility_space, "!{{ {}\n{} }}".format(dafltr_t, dafltr_maybe))
            self.assertMatch(True, possibility_space, "[{}\n{}]".format(dafltr_t, dafltr_maybe))
            self.assertMatch(False, possibility_space, "![{}\n{}]".format(dafltr_t, dafltr_maybe))

        for dafltr_f, dafltr_maybe in itertools.product(wont_match, might_match):
            self.assertMatch(False, possibility_space, "{}\n{}".format(dafltr_f, dafltr_maybe))
            self.assertMatch(True, possibility_space, "!{{ {}\n{} }}".format(dafltr_f, dafltr_maybe))
            self.assertMatch(None, possibility_space, "[{}\n{}]".format(dafltr_f, dafltr_maybe))
            self.assertMatch(None, possibility_space, "![{}\n{}]".format(dafltr_f, dafltr_maybe))


# input, expected_dense, expected_pretty
PRETTY_PRINT_EXPECTATIONS = (

# Simple
[
'''
    val1 = 10
    val2 = 20
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Simple with a comment
[
'''
    val1 = 10 # comment 1
    # comment 2
    val2 = 20
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10 # comment 1
  # comment 2
  "val2" = 20
}
'''.strip()
],

# Comment at the end
[
'val1 = 10\n# comment 2',
'{"val1"=10}',
'''
{
  "val1" = 10
  # comment 2
}
'''.strip()
],

# Only a comment
[
'# comment 1',
'{}',
'''
{
  # comment 1
}
'''.strip()
],

# Simple array lookup
[
'''
    val in (10, 20)
''',
'{"val"in(10,20)}',
'''
{
  "val" in (
    10
    20
  )
}
'''.strip()
],

# Simple string array lookup
[
'''
    val in ("abc", "xyz")
''',
'{"val"in("abc","xyz")}',
'''
{
  "val" in (
    "abc"
    "xyz"
  )
}
'''.strip()
],

# Simple Timestamp lookup
[
'''
    val1 = timestamp(2017-08-03)
    val2 = timestamp(2017-08-03 15:21)
''',
'{"val1"=timestamp(2017-08-03),"val2"=timestamp(2017-08-03 15:21)}',
'''
{
  "val1" = timestamp(2017-08-03)
  "val2" = timestamp(2017-08-03 15:21)
}
'''.strip()
],

# Array Timestamp lookup
[
'''
    val1 in (timestamp(2017-08-03), timestamp(2017-08-03 20:32))
''',
'{"val1"in(timestamp(2017-08-03),timestamp(2017-08-03 20:32))}',
'''
{
  "val1" in (
    timestamp(2017-08-03)
    timestamp(2017-08-03 20:32)
  )
}
'''.strip()
],


# Simple boolean array lookup
[
'''
    val in (true, false)
''',
'{"val"in(true,false)}',
'''
{
  "val" in (
    true
    false
  )
}
'''.strip()
],

# Simple single-item array lookup
[
'''
    val1 in ("abc")
    val2 !in ("xyz")
    val3 in (1)
    val4 !in (2)
    val5 in (true)
    val6 !in (false)
''',
'{"val1"in("abc"),"val2"!in("xyz"),"val3"in(1),"val4"!in(2),"val5"in(true),"val6"!in(false)}',
'''
{
  "val1" in (
    "abc"
  )
  "val2" !in (
    "xyz"
  )
  "val3" in (
    1
  )
  "val4" !in (
    2
  )
  "val5" in (
    true
  )
  "val6" !in (
    false
  )
}
'''.strip()
],

# Simple - out of order
[
'''
    val2 = 20
    val1 = 10
''',
'{"val2"=20,"val1"=10}',
'''
{
  "val2" = 20
  "val1" = 10
}
'''.strip()
],

# Explicit All
[
'''
{
    val1 = 10
    val2 = 20
}
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Not All
[
'''
!{
    val1 = 10
    val2 = 20
}
''',
'!{"val1"=10,"val2"=20}',
'''
!{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Unnecessary nested All
[
'''
{
  {
    val1 = 10
    val2 = 20
  }
}
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Unnecessary nested Not All
[
'''
{
  !{
    val1 = 10
    val2 = 20
  }
}
''',
'!{"val1"=10,"val2"=20}',
'''
!{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Unnecessary nested All (inside an any)
[
'''
[
  {
    val1 = 10
    val2 = 20
  }
]
''',
'{"val1"=10,"val2"=20}',
'''
{
  "val1" = 10
  "val2" = 20
}
'''.strip()
],

# Simple Any
[
'''
[
    val1 = 10
    val2 = 20
]
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],

# Not Any
[
'''
![
    val1 = 10
    val2 = 20
]
''',
'!["val1"=10,"val2"=20]',
'''
![
  "val1" = 10
  "val2" = 20
]
'''.strip()
],



# Unnecessary nested Any
[
'''
[
  [
    val1 = 10
    val2 = 20
  ]
]
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],

# Unnecessary nested Any (inside an all)
[
'''
{
  [
    val1 = 10
    val2 = 20
  ]
}
''',
'["val1"=10,"val2"=20]',
'''
[
  "val1" = 10
  "val2" = 20
]
'''.strip()
],

# simple + nested Any inside an all
[
'''
{
  val1 = 10
  [
    val2 = 20
    val3 = 30
  ]
}
''',
'{"val1"=10,["val2"=20,"val3"=30]}',
'''
{
  "val1" = 10
  [
    "val2" = 20
    "val3" = 30
  ]
}
'''.strip()
],

# simple + nested (negative) array lookup inside an all
[
'''
{
  val1 = 10
  val2 !in (20, 30)
}
''',
'{"val1"=10,"val2"!in(20,30)}',
'''
{
  "val1" = 10
  "val2" !in (
    20
    30
  )
}
'''.strip()
],

# simple + nested All inside an Any
[
'''
[
  val1 = 10
  {
    val2 = 20
    val3 = 30
  }
]
''',
'["val1"=10,{"val2"=20,"val3"=30}]',
'''
[
  "val1" = 10
  {
    "val2" = 20
    "val3" = 30
  }
]
'''.strip()
],

[
r'v="a"',
r'{"v"="a"}',
'''
{
  "v" = "a"
}
'''.strip(),
],

# Escaped double quote
[
r'v="\"a"',
r'{"v"="\"a"}',
'''
{
  "v" = "\\"a"
}
'''.strip(),
],

# Escaped single quote
[
r"v='\'a'",
'{"v"="\'a"}',
'''
{
  "v" = "'a"
}
'''.strip(),
],

# Daffodil separated with carraige return, line feed
[
u'"metropcs_precamp_qxthanks" ?= true\r\n"source" != "test"',
u'{"metropcs_precamp_qxthanks"?=true,"source"!="test"}',
'''
{
  "metropcs_precamp_qxthanks" ?= true
  "source" != "test"
}
'''.strip()
],

# Complex, unordered, badly indented and nested
[
'''
val2 = 3
val2 ?= true
    val1 < 10
  val9 = "what's \\"up\\"?"
[
  {
val6 ?= true
      val5 = 30
    }
       # words!
  {
    val5 ?= true
    val5 != 30
  }, val99 < 5.525 ]

''',
'{"val2"=3,"val2"?=true,"val1"<10,"val9"="what\'s \\"up\\"?",[{"val6"?=true,"val5"=30},{"val5"?=true,"val5"!=30},"val99"<5.525]}',
'''
{
  "val2" = 3
  "val2" ?= true
  "val1" < 10
  "val9" = "what's \\"up\\"?"
  [
    {
      "val6" ?= true
      "val5" = 30
    }
    # words!
    {
      "val5" ?= true
      "val5" != 30
    }
    "val99" < 5.525
  ]
}
'''.strip()
],

)

class PrettyPrintingTests(unittest.TestCase):
    delegate_dense = PrettyPrintDelegate(dense=True)
    delegate_pretty = PrettyPrintDelegate(dense=False)

    def pp(self, fltr):
        dense = Daffodil(fltr, delegate=self.delegate_dense)()
        pretty = Daffodil(fltr, delegate=self.delegate_pretty)()
        return dense, pretty

    def assertFilterIsCorrect(self, fltr, expected_dense, expected_pretty):
        dense, pretty = self.pp(fltr)
        self.assertEqual(dense, expected_dense)
        self.assertEqual(pretty, expected_pretty)

    def test_simple(self):
        for fltr, dense, pretty in PRETTY_PRINT_EXPECTATIONS:
            self.assertFilterIsCorrect(fltr, dense, pretty)

    def test_multiple_passthroughs(self):
        regexp_py_comment = re.compile('#.*?(\n|$)')

        for fltr, dense_expected, pretty_expected in PRETTY_PRINT_EXPECTATIONS:
            d1, p1 = self.pp(fltr)
            d1_dense, d1_pretty = self.pp(d1)
            p1_dense, p1_pretty = self.pp(p1)

            self.assertEqual(p1_pretty, pretty_expected)
            self.assertEqual(d1_dense, dense_expected)
            self.assertEqual(p1_dense, dense_expected)

            # don't check re-printing dense as pretty if there are comments because
            # the comments are discarded by dense version
            if not regexp_py_comment.search(fltr):
                self.assertEqual(d1_pretty, pretty_expected)


# Borrowed gratuitously from https://gist.github.com/k4ml/2219751
from os import path as osp

def rel_path(*p):
    return osp.normpath(osp.join(rel_path.path, *p))

rel_path.path = osp.abspath(osp.dirname(__file__))
this = osp.splitext(osp.basename(__file__))[0]

from django.conf import settings
SETTINGS = dict(
    SITE_ID=1,
    DATABASES = {
        'default':{
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'daffodil_hstore_test',
            'USER': "postgres",
            'HOST': '127.0.0.1',
            'PORT': 5432,
        }
    },
    DEBUG=True,
    TEMPLATE_DEBUG=True,
    INSTALLED_APPS=[
        "django.contrib.postgres",
        "testapp",
    ],
    ROOT_URLCONF=this,
    MIDDLEWARE_CLASSES=(),
)

if not settings.configured:
    settings.configure(**SETTINGS)

import django
try:
    django.setup()
except AttributeError:
    pass


from daffodil.hstore_predicate import HStoreQueryDelegate
from testapp.models import BasicHStoreData


class SATDataTestsWithHStore(SATDataTests):

    def setUp(self):
        self.d = BasicHStoreData.objects.all()

    def filter(self, daff_src):
        delegate = HStoreQueryDelegate(hstore_field_name="hsdata")
        daff = Daffodil(daff_src, delegate=delegate)
        return daff(self.d)

    def test_none(self):
        pass


from django.core import management

if __name__ == "__main__":
    management.call_command("migrate")

    BasicHStoreData.objects.all().delete()
    for record in load_test_data('nyc_sat_scores'):
        BasicHStoreData.objects.create(hsdata=record)

    unittest.main()

