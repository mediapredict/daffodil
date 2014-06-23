from django.db import models
from django_hstore import hstore

print "Import OK...."

class SomeModel(models.Model):
    cname = models.CharField(max_length=255,
                               help_text="needs to match the question id, (e.g., mp_birth_year)")
    hstore_col = hstore.DictionaryField()
    objects = hstore.HStoreManager()
    #hstore_col = models.CharField(max_length=255)

    # class Meta:
    #     app_label = 'test'