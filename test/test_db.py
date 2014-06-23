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
from dbmodel import models

class SomeModelCase(TestCase):
    def setUp(self):
        td = "a"
        models.SomeModel.objects.create(cname="1", hstore_col =td )
        models.SomeModel.objects.create(cname="2", hstore_col =td)

    def test_animals_can_speak(self):
        """Some record is stored"""
        self.assertEqual( len(models.SomeModel.objects.filter( cname="1" )), 1)
        pass

if __name__ == "__main__":

    from django.core.management import call_command
    call_command('syncdb', interactive=False)

    # from django.test.simple import DjangoTestSuiteRunner
    # DjangoTestSuiteRunner().setup_databases()

    from django.test.utils import setup_test_environment
    setup_test_environment()

    unittest.main()