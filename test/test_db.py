#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from django.conf import settings
settings.configure(DEBUG = True,
               DATABASES = {'default' :
                                {
                                    'ENGINE':   'django.db.backends.postgresql_psycopg2',
                                    'NAME':     "df",
                                    'USER':     "postgres",
                                    'PASSWORD': "postgres",
                                    'HOST':     "localhost",
                                    'TEST_NAME': 'df',
                                    },
                            },
               INSTALLED_APPS = (
                    'django_hstore',
                    'dbmodel',
               )
)



from django.test import TestCase
from django.db import models
from django_hstore import hstore
from dbmodel.models import SomeModel
from dbmodel.models import NYCSatScores

from daffodil import Daffodil
from daffodil.exceptions import ParseError
from daffodil.django_hstore import HStoreQueryDelegate

from test import load_test_data#, SATDataTests
from django.db.models import Q

class SomeModelCase(TestCase):
#class SomeModelCase(SATDataTests):

    def setUp(self):
        data_dicts = load_test_data('nyc_sat_scores')
        for d in data_dicts:
            NYCSatScores(cname="testing hstore", hstore_col=d).save()

        self.d = NYCSatScores.objects.all()

    def filter(self, daff_src):
        return Daffodil(daff_src, delegate=HStoreQueryDelegate("hstore_col") )(self.d)

    def assert_filter_has_n_results(self, n, daff_src):
        self.assertEqual(len(self.filter(daff_src)), n)


    def test_no_filters(self):
        self.assertEqual(len(self.d), 421)

    def test_empty(self):
        # self.assert_filter_has_n_results(421, "")
        # self.assert_filter_has_n_results(421, "{}")
        self.assert_filter_has_n_results(0, "[]")

    def test_int_eq(self):
        self.assert_filter_has_n_results(4, """
            num_of_sat_test_takers = 50
        """)
    def test_int_ne(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != 50
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

    def test_int_lte(self):
        self.assert_filter_has_n_results(148, """
            num_of_sat_test_takers <= 50
        """)

    def test_float_eq(self):
        self.assert_filter_has_n_results(0, """
            num_of_sat_test_takers = 50.5
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
        self.assert_filter_has_n_results(417, """
            'num_of_sat_test_takers' != '50'
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

    def test_string_ne(self):
        self.assert_filter_has_n_results(420, """
            school_name != "EAST SIDE COMMUNITY SCHOOL"
        """)
        self.assert_filter_has_n_results(420, """
            school_name != 'EAST SIDE COMMUNITY SCHOOL'
        """)
    def test_comparing_a_string_containing_int(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != "50"
        """)

    def test_comparing_a_string_containing_float(self):
        self.assert_filter_has_n_results(417, """
            num_of_sat_test_takers != "50.0"
        """)

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
        # FAILS this is feature of postgres, soon as it notices unknown field there are zero results
        self.assert_filter_has_n_results(421, """
            "number of SAT Test Takers 9-17-2013" != 99
        """)
    def test_invalid_filter(self):
        self.assertRaises(ParseError, Daffodil, """
            [
        """)

    def test_unicode_filter(self):
        self.assert_filter_has_n_results(273, u"""
            num_of_sat_test_takers > 50
        """)

    def test_existance_has_value(self):
        self.assert_filter_has_n_results(421, u"""
            num_of_sat_test_takers ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            num_of_sat_test_takers ?= false
        """)
        self.assert_filter_has_n_results(421, u"""
            "num_of_sat_test_takers" ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            "num_of_sat_test_takers" ?= false
        """)
        self.assert_filter_has_n_results(421, u"""
            'num_of_sat_test_takers' ?= true
        """)
        self.assert_filter_has_n_results(0, u"""
            'num_of_sat_test_takers' ?= false
        """)
    def test_existance_does_not_have_value(self):
        self.assert_filter_has_n_results(0, u"""
            asdf ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            asdf ?= false
        """)
        self.assert_filter_has_n_results(0, u"""
            "asdf" ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            "asdf" ?= false
        """)
        self.assert_filter_has_n_results(0, u"""
            'asdf' ?= true
        """)
        self.assert_filter_has_n_results(421, u"""
            'asdf' ?= false
        """)
if __name__ == "__main__":
    #
    # ids = (n.id for n in NYCSatScores.objects.all())
    # for id in ids:
    #     n = NYCSatScores.objects.get( pk= id)
    #     n.delete()
    #     n.save()


    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()


