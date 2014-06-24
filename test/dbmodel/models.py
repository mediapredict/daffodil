from django.db import models
from django_hstore import hstore

class NYCSatScores(models.Model):
    cname = models.CharField(max_length=255)
    hstore_col = hstore.DictionaryField()
    objects = hstore.HStoreManager()