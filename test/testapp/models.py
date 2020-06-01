from django.db import models
from django.contrib.postgres.fields import HStoreField


class BasicHStoreData(models.Model):
    hsdata = HStoreField()
