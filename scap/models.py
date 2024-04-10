import os
from datetime import datetime
from django.contrib.gis.db import models

from django.contrib.auth.models import User


def aoi_upload_path(instance, filename):
    return '/'.join(['uploads', str(instance.owner.username), 'aoi', instance.name, filename])


def agb_upload_path(instance, filename):
    return '/'.join(['uploads', str(instance.owner.username), 'agb', instance.name, filename])


def fc_upload_path(instance, filename):
    return '/'.join(['uploads', instance.collection.owner.username, 'fc', instance.collection.name, filename])


class CurrentTask(models.Model):
    id = models.CharField(max_length=100, default="", help_text="Task ID", primary_key=True)
    overall_progress = models.FloatField(default=0.0, help_text="Overall Progress")
    subprocess_progress = models.FloatField(default=0.0, help_text="Current Process Progress")
    description = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name_plural = "Running Tasks"


class ForestCoverCollection(models.Model):
    ACCESS_CHOICES = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    PROCESSING_STATES = (
        ('Not Processed', 'Not Processed'),
        ('Staged', 'Staged'),
        ('In Progress', 'In Progress'),
        ('Processed', 'Processed')
    )

    name = models.CharField(max_length=100, default="", help_text="Forest Cover Collection Name")
    description = models.TextField(default="", help_text="Forest Cover Collection Description")

    doi_link = models.CharField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)

    boundary_file = models.FileField(max_length=254, help_text="Boundary File", null=True, blank=True)

    access_level = models.CharField(max_length=10, default="Select", help_text="Access Level", choices=ACCESS_CHOICES)

    owner = models.ForeignKey(User, verbose_name="Uploaded By", on_delete=models.CASCADE)
    processing_status = models.CharField(max_length=100, default="Not Processed", help_text="Processing Status", choices=PROCESSING_STATES)

    processing_task = models.ForeignKey(CurrentTask, verbose_name="Current Processing Task", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "Forest Cover Collections"
        unique_together='name','owner'


class ForestCoverFile(models.Model):
    file = models.FileField(upload_to=fc_upload_path)
    year = models.IntegerField(default=0, help_text="Year")
    collection = models.ForeignKey(ForestCoverCollection, on_delete=models.CASCADE, related_name='yearly_files')
    doi_link = models.CharField(max_length=100, default="", blank=True)
    metadata_link = models.URLField(max_length=100, default="", blank=True)

    def filename(self):
        return os.path.basename(self.file.name)


    class Meta:
        verbose_name_plural = "Forest Cover Files"


class AOICollection(models.Model):
    ACCESS_CHOICES = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    PROCESSING_STATES = (
        ('Not Processed', 'Not Processed'),
        ('Staged', 'Staged'),
        ('In Progress', 'In Progress'),
        ('Processed', 'Processed')
    )

    name = models.CharField(max_length=100, default="", help_text="AOI name")
    description = models.TextField(default="", help_text="AOI description")

    doi_link = models.CharField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)

    source_file = models.FileField(upload_to=aoi_upload_path)

    owner = models.ForeignKey(User, verbose_name="Uploaded By", on_delete=models.CASCADE)

    access_level = models.CharField(max_length=10, default="Private", help_text="Access Level", choices=ACCESS_CHOICES)
    processing_status = models.CharField(max_length=100, default="Not Processed", help_text="Processing Status", choices=PROCESSING_STATES)

    processing_task = models.ForeignKey(CurrentTask, verbose_name="Current Processing Task", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "AOI Collections"
        unique_together = 'name', 'owner'


class AOIFeature(models.Model):
    collection = models.ForeignKey(AOICollection, null=True, on_delete=models.CASCADE, related_name='features')

    wdpa_pid = models.CharField(max_length=52)
    name = models.CharField(max_length=254)
    orig_name = models.CharField(max_length=254)
    desig_eng = models.CharField(max_length=254, null=True)
    desig_type = models.CharField(max_length=20, null=True)
    rep_area = models.FloatField()
    gis_area = models.FloatField()
    iso3 = models.CharField(max_length=50)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Individual AOIs"


class AGBCollection(models.Model):
    ACCESS_CHOICES = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    PROCESSING_STATES = (
        ('Not Processed', 'Not Processed'),
        ('Staged', 'Staged'),
        ('In Progress', 'In Progress'),
        ('Processed', 'Processed')
    )

    name = models.CharField(max_length=100, default="", help_text="Collection Name")
    description = models.CharField(max_length=100, default="", help_text="Collection Description")

    doi_link = models.CharField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)

    boundary_file = models.FileField(upload_to=agb_upload_path, null=True, blank=True)
    source_file = models.FileField(upload_to=agb_upload_path)

    year = models.IntegerField(default=0, help_text="Calibration Year")

    owner = models.ForeignKey(User, verbose_name="Uploaded By", on_delete=models.CASCADE)

    access_level = models.CharField(max_length=10, default="Private", help_text="Access Level", choices=ACCESS_CHOICES)
    processing_status = models.CharField(max_length=100, default="Not Processed", help_text="Processing Status", choices=PROCESSING_STATES)

    processing_task = models.ForeignKey(CurrentTask, verbose_name="Current Processing Task", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name_plural = "AGB Collections"
        unique_together = 'name', 'owner'
        
class CarbonStatistic(models.Model):
    fc_index = models.ForeignKey(ForestCoverCollection, verbose_name="Forest Cover Source", on_delete=models.CASCADE)
    agb_index = models.ForeignKey(AGBCollection, verbose_name="AGB Source", on_delete=models.CASCADE)
    aoi_index = models.ForeignKey(AOIFeature, default=1, help_text="AOI the calculation was made for", on_delete=models.CASCADE)
    year_index = models.IntegerField(help_text="Year")

    final_carbon_stock = models.FloatField(help_text="Carbon Stock")
    emissions = models.FloatField(help_text="Emissions")
    agb_value = models.FloatField(help_text="Total AGB")

    processing_time = models.FloatField(
        help_text="Zonal Statistics Processing Time (seconds)",
        blank=True, null=True)

    class Meta:
        verbose_name_plural = "Carbon Statistics"


class ForestCoverStatistic(models.Model):
    fc_index = models.CharField(max_length=100, default="", help_text="FC File")
    aoi_index = models.ForeignKey(AOIFeature, default=1, help_text="AOI the calculation was made for", on_delete=models.CASCADE)
    year_index = models.IntegerField(help_text="Calculation Year")

    final_forest_area = models.FloatField(help_text="Final Forest Area")
    forest_gain = models.FloatField(help_text="Forest Gain")
    forest_loss = models.FloatField(help_text="Forest Loss")

    processing_time = models.FloatField(
        help_text="Zonal Statistics Processing Time (seconds)",
        blank=True, null=True)

    def net_forest_change(self):
        return self.forest_gain - self.forest_loss

    class Meta:
        verbose_name_plural = "Forest Cover Statistics"


class PilotCountry(models.Model):
    country_name = models.CharField(max_length=100, default="", help_text="Country Name")
    country_code = models.CharField(max_length=3, default="", help_text="Country Code (ISO 3)")
    hero_image = models.ImageField(upload_to='assets/img/pilotcountry/', help_text="Hero Image")
    region = models.CharField(max_length=100, default="", help_text="Region")
    country_description = models.TextField(default="", help_text="Country Description")
    year_added = models.IntegerField(help_text="Year Added as Pilot Country", default=2024)
    aoi_polygon = models.ForeignKey(AOIFeature, help_text="Country Polygon AOI ID (reference to AOI model)",
                                    on_delete=models.CASCADE, blank=True, null=True)
    latitude = models.FloatField(default=0, help_text="Latitude")
    longitude = models.FloatField(default=0, help_text="Longitude")
    zoom_level = models.IntegerField(default=0, help_text="Default Zoom level")
    forest_cover_collection = models.ForeignKey(ForestCoverCollection, help_text="Default Forest Cover Collection to show on map",blank=True,null=True,on_delete=models.CASCADE)

    def __str__(self):
        return self.country_name

    def country_label(self):
        return "Country" + self.id

    class Meta:
        verbose_name_plural = "Pilot Countries"