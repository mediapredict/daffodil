from django.db import models
from django_hstore import hstore


class BasicHStoreData(models.Model):
    hsdata = hstore.DictionaryField()
    objects = hstore.HStoreManager()