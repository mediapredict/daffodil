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
        # converted_ints = []
        # for d in data_dicts:
        #     converted_ints.append( dict( (k, self.to_n_dig_int(v) ) for k, v in d.items() ) )

        # for d in converted_ints:
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
        self.assert_filter_has_n_results(421, "")
        self.assert_filter_has_n_results(421, "{}")
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

if __name__ == "__main__":

    ids = (n.id for n in NYCSatScores.objects.all())
    for id in ids:
        n = NYCSatScores.objects.get( pk= id)
        n.delete()
        n.save()


    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()


