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


class SomeModelCase(TestCase):


    def test_basic_hstore(self):
        instance = SomeModel.objects.create(cname='something', hstore_col={'a': '1', 'b': '2'})
        assert instance.hstore_col['a'] == '1'

    def test_basic_hstore_with_filter_1(self):
        instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '5', 'second': '2'})
        instance.save()

        assert SomeModel.objects.filter( hstore_col__contains={'first': '5', 'second': '2'} )

    def test_basic_hstore_with_contains_key(self):
        instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '10', 'second': '20'})
        instance.save()
        assert len( SomeModel.objects.filter( hstore_col__contains='first' ))>0

    def test_basic_hstore_with_contains_value(self):
        instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '55', 'second': '77'})
        instance.save()
        assert len( SomeModel.objects.filter( hstore_col__contains='55' ))>0

    def test_basic_hstore_with_gt_value(self):
        instance = SomeModel.objects.create(cname='something_else', hstore_col={'first': '55', 'second': '77'})
        instance.save()
        assert len( SomeModel.objects.filter( hstore_col__gt={'first': '5'} ))>0

    def test_basic_hstore_with_get(self):
        instance = SomeModel.objects.create(cname='something_else245', hstore_col={'first': '100', 'second': '200'})
        assert SomeModel.objects.get( cname="something_else245").hstore_col['first'] == '100'

    def test_basic_hstore_with_q(self):
        from django.db.models import Q
        instance = SomeModel.objects.create(cname='something_else245', hstore_col={'first': '100', 'second': '200'})
        instance.save()
        assert SomeModel.objects.filter( Q(hstore_col__gte= {'first':'100'}) | Q(hstore_col__lt= {'second':'100'}) )

if __name__ == "__main__":

    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    # from django.test.simple import DjangoTestSuiteRunner
    # DjangoTestSuiteRunner().setup_databases()

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()