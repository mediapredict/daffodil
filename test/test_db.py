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

    def to_n_dig_int(num, digits=6):
        num_str = "%0" + str(digits) + "d"
        if isinstance(num, str):
            return num_str % int(num) if num.isdigit() else num
        else:
            return num_str % num

    def filter(self, daff_src):
        return Daffodil(daff_src, delegate=HStoreQueryDelegate("hstore_col") )(self.d)

    def assert_filter_has_n_results(self, n, daff_src):
        self.assertEqual(len(self.filter(daff_src)), n)

    # def test_no_filters(self):
    #     self.assertEqual(len(self.d), 421)
    #
    # def test_empty(self):
    #     self.assert_filter_has_n_results(421, "")
    #
    # def test_empty2(self):
    #     self.assert_filter_has_n_results(421, "")
    #
    # def test_empty3(self):
    #     self.assert_filter_has_n_results(421, "{}")
    #
    # def test_int_eq(self):
    #     self.assert_filter_has_n_results(4, """
    #         num_of_sat_test_takers = 50
    #     """)

    # def test_int_gt(self):
    #     self.assert_filter_has_n_results(10, """
    #         sat_writing_avg_score > 100
    #     """)
    #
    def test_int_eq_one(self):

        import time
        start = time.time()
        some_list = NYCSatScores.objects.extra(where=["(hstore_col->'sat_writing_avg_score')::integer >0"])
        print "*"*40
        print len( some_list )
        end = time.time()
        print end - start
        print "*"*40
        b = len( NYCSatScores.objects.filter( hstore_col__gt={'sat_writing_avg_score': '000099' } ))>0
        # self.assert_filter_has_n_results(1, """
        #     sat_writing_avg_score = 628
        # """)

    #
    # hstore
    #
    # def test_basic_hstore(self):
    #     instance = SomeModel.objects.create(cname='something', hstore_col={'a': '1', 'b': '2'})
    #     assert instance.hstore_col['a'] == '1'
    #
    # def test_basic_hstore_with_filter_1(self):
    #     instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '5', 'second': '2'})
    #     instance.save()
    #
    #     assert SomeModel.objects.filter( hstore_col__contains={'first': '5', 'second': '2'} )
    #
    # def test_basic_hstore_with_contains_key(self):
    #     instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '10', 'second': '20'})
    #     instance.save()
    #     assert len( SomeModel.objects.filter( hstore_col__contains='first' ))>0
    #
    # def test_basic_hstore_with_contains_value(self):
    #     instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '55', 'second': '77'})
    #     instance.save()
    #     assert len( SomeModel.objects.filter( hstore_col__contains='55' ))>0
    #
    # def test_basic_hstore_with_gt_value(self):
    #     instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '55', 'second': '77'})
    #     instance.save()
    #     assert len( SomeModel.objects.filter( hstore_col__gt={'first': '54'} ))>0
    #
    # def test_basic_hstore_with_get(self):
    #     instance = SomeModel.objects.create(cname='something_else245', hstore_col={'first': '100', 'second': '200'})
    #     assert SomeModel.objects.get( cname="something_else245").hstore_col['first'] == '100'
    #
    # def test_basic_hstore_with_q(self):
    #     from django.db.models import Q
    #     instance = SomeModel.objects.create(cname='something_else245', hstore_col={'first': '100', 'second': '200'})
    #     instance.save()
    #     assert SomeModel.objects.filter( Q(hstore_col__gte= {'first':'100'}) | Q(hstore_col__lt= {'second':'100'}) )

if __name__ == "__main__":

    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()


