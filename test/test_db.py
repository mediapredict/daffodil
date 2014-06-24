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
from dbmodel.models import NYCSatScores

from daffodil import Daffodil
from daffodil.exceptions import ParseError
from daffodil.django_hstore import HStoreQueryDelegate

from test import load_test_data, SATDataTests
from django.db.models import Q

class HStoreModelCase(SATDataTests, TestCase):

    def setUp(self):
        data_dicts = load_test_data('nyc_sat_scores')
        for d in data_dicts:
            NYCSatScores(cname="testing hstore", hstore_col=d).save()

        self.d = NYCSatScores.objects.all()

    def filter(self, daff_src):
        return Daffodil(daff_src, delegate=HStoreQueryDelegate("hstore_col") )(self.d)


if __name__ == "__main__":

    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()


