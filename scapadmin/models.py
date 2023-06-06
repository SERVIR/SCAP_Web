import uuid

from django.db import models


class LC(models.Model):
    lc_id = models.CharField(max_length=10, primary_key=True,
                             help_text="LC ID number")

class AGB(models.Model):
    agb_id = models.CharField(max_length=10, primary_key=True,
                              help_text="AGB ID number")

class Value(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lc_id = models.ForeignKey(LC, default=1, verbose_name="LandCover", on_delete=models.SET_DEFAULT)
    agb_id = models.ForeignKey(AGB, default=1, verbose_name="AGB", on_delete=models.SET_DEFAULT)
    year = models.IntegerField(help_text="Year")
    lc_agb_value = models.FloatField(help_text="Value")


class Predefined_AOI(models.Model):
    aoi_id = models.CharField(max_length=10, primary_key=True,
                              help_text="AOI ID number")
    aoi_name = models.CharField(max_length=100, default="", help_text="AOI Year")
    aoi_country = models.IntegerField(help_text="AOI Year")
