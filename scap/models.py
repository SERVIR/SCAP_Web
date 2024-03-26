import os
from datetime import datetime
from django.contrib.gis.db import models
from colorfield.fields import ColorField
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator

from ScapTestProject.settings import UPLOAD_ROOT


class PredefinedAOI(models.Model):
    # aoi_id = models.CharField(max_length=10, primary_key=True,
    #                           help_text="AOI ID number")
    aoi_name = models.CharField(max_length=100, default="", help_text="AOI Name")
    aoi_country = models.CharField(max_length=2, help_text="AOI Country")
    aoi_geom = models.MultiPolygonField()

    def __str__(self):
        return self.aoi_name

    def aoi_label(self):
        return "AOI" + str(self.id)


class BoundaryFiles(models.Model):
    feature_id = models.IntegerField()
    name_es = models.CharField(max_length=17)
    nomedep = models.CharField(max_length=1, null=True)
    nomemun = models.CharField(max_length=1, null=True)
    pais = models.CharField(max_length=17)
    fid = models.CharField(max_length=20)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.name_es

    class Meta:
        verbose_name_plural = "BoundaryFiles"


class AOI(models.Model):
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
        verbose_name_plural = "Predefined AOIs"


class PilotCountry(models.Model):
    country_name = models.CharField(max_length=100, default="", help_text="Country Name")
    country_code = models.CharField(max_length=2, default="", help_text="Country Code (ISO 2)")
    hero_image = models.ImageField(upload_to='assets/img/pilotcountry/', help_text="Hero Image")
    region = models.CharField(max_length=100, default="", help_text="Region")
    country_description = models.TextField(default="", help_text="Country Description")
    year_added = models.IntegerField(help_text="Year Added as Pilot Country", default=2024)
    aoi_polygon = models.ForeignKey(AOI, help_text="Country Polygon AOI ID (reference to AOI model)",
                                    on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.country_name

    def country_label(self):
        return "Country" + self.id

    class Meta:
        verbose_name_plural = "Pilot Countries"


class ForestCoverChange(models.Model):
    fc_source = models.ForeignKey(BoundaryFiles, help_text="Forest Cover Source", on_delete=models.CASCADE)
    aoi = models.ForeignKey(AOI, default=1, help_text="AOI the calculation was made for", on_delete=models.CASCADE)
    year = models.IntegerField(help_text="Year the change was calculated for")
    baseline_year = models.IntegerField(help_text="Baseline Year for forest cover change calculation", blank=True,
                                        null=True)
    initial_forest_area = models.FloatField(help_text="Initial forest area for baseline year")
    forest_gain = models.FloatField(help_text="Forest Gain", null=True)
    forest_loss = models.FloatField(help_text="Forest Loss")
    processing_time = models.FloatField(
        help_text="Time to calculate forest change data for this time period, AOI and Forest Cover Change source (seconds)",
        blank=True, null=True)

    def net_forest_change(self):
        return self.forest_gain - self.forest_loss


class ForestCoverChangeFile(models.Model):
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    fc_source = models.ForeignKey(BoundaryFiles, help_text="Forest Cover Source", on_delete=models.CASCADE)
    year = models.IntegerField(help_text="Year the change was calculated for")
    baseline_year = models.IntegerField(help_text="Baseline year for forest cover change calculation", blank=True,
                                        null=True)
    created = models.DateTimeField(help_text='Date and time the file was created', auto_now_add=True)
    processing_time = models.FloatField(help_text="Time to generate the file (seconds)", blank=True, null=True)
    file_name = models.CharField(max_length=200, default="", help_text="Forest Cover Change file name")
    file_directory = models.CharField(max_length=200, default="", help_text="Forest Cover Change file directory")

    class Meta:
        verbose_name_plural = "Forest Cover Change Files"


class ForestCoverFile(models.Model):
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    fc_source = models.ForeignKey(BoundaryFiles, help_text="Forest Cover Source", on_delete=models.CASCADE)
    file_name = models.CharField(max_length=100, default="", help_text="Forest Cover Source file name")
    file_directory = models.CharField(max_length=100, default="", help_text="Forest Cover Source file directory")
    created = models.DateTimeField(help_text='Date and time the file was created', auto_now_add=True)

    class Meta:
        verbose_name_plural = "Forest Cover Files"


class ForestCoverCollection(models.Model):
    ACCESS_CHOICES = (
        ('Select', 'Select'),
        ('Public', 'Public'),  # First one is the value of select option and second is the displayed value in option
        ('Private', 'Private'),
    )
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    collection_name = models.CharField(max_length=100, default="", help_text="Collection name", unique=True)
    collection_description = models.TextField(default="", help_text="Collection Description")
    boundary_file = models.FileField(max_length=254, upload_to='uploads/%Y/%m/%d/', help_text="Boundary File")
    access_level = models.CharField(max_length=10, default="Select", help_text="Access Level", choices=ACCESS_CHOICES)
    projection = models.CharField(max_length=100, default="", help_text="Projection")
    resolution = models.FloatField(max_length=100, default="", help_text="Resolution")
    username = models.CharField(max_length=100, default="", help_text="Username")
    doi_link = models.URLField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)
    last_accessed_on = models.DateTimeField(default=datetime.now)
    processing_status = models.CharField(max_length=100, default="Not processed", help_text="Processing Status")

    class Meta:
        verbose_name_plural = "FC_UserCollection"


class TiffFile(models.Model):
    upload_storage = FileSystemStorage(location=UPLOAD_ROOT, base_url='/tifffiles')
    file = models.FileField(storage=upload_storage, upload_to='uploads/%Y/%m/%d/')
    year = models.IntegerField(default=0, help_text="Year")
    collection = models.ForeignKey(ForestCoverCollection, on_delete=models.CASCADE)
    doi_link = models.URLField(max_length=100, default="", blank=True)
    metadata_link = models.URLField(max_length=100, default="", blank=True)

    def filename(self):
        return os.path.basename(self.file.name)


# class TiffFile(models.Model):
#     tiff_file = models.FileField(upload_to=None)
# collection = models.ForeignKey(NewCollection, on_delete=models.CASCADE, related_name='tiff_files',default=None)

class AOICollection(models.Model):
    upload_storage = FileSystemStorage(location=UPLOAD_ROOT, base_url='/aoifiles')
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    aoi_name = models.CharField(max_length=100, default="", unique=True, help_text="AOI name")
    aoi_description = models.TextField(default="", help_text="AOI description")
    doi_link = models.URLField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)
    aoi_shape_file = models.FileField(storage=upload_storage, upload_to='aoi_uploads/%Y/%m/%d/')
    username = models.CharField(max_length=100, default="", help_text="Username")
    last_accessed_on = models.DateTimeField(default=datetime.now)
    processing_status = models.CharField(max_length=100, default="Not processed", help_text="Processing Status")

    class Meta:
        verbose_name_plural = "AOI_UserCollection"


class AGBCollection(models.Model):
    upload_storage = FileSystemStorage(location=UPLOAD_ROOT, base_url='/agbfiles')
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    agb_name = models.CharField(max_length=100, default="", unique=True, help_text="AGB name")
    agb_description = models.CharField(max_length=100, default="", unique=True, help_text="AGB description")
    doi_link = models.URLField(max_length=200, default="", blank=True)
    metadata_link = models.URLField(max_length=200, default="", blank=True)
    agb_boundary_file = models.FileField(storage=upload_storage, upload_to='agb_uploads/%Y/%m/%d/')
    agb_tiff_file = models.FileField(storage=upload_storage, upload_to='agb_uploads/%Y/%m/%d/')
    username = models.CharField(max_length=100, default="", help_text="Username")
    last_accessed_on = models.DateTimeField(default=datetime.now)
    processing_status = models.CharField(max_length=100, default="Not processed", help_text="Processing Status")


class ForestCoverSource(models.Model):
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    fcs_name = models.CharField(max_length=100, default="", help_text="Forest Cover Data Source Name")
    fcs_color = ColorField(default="#FF0000")
    fcs_description = models.TextField(default="", help_text="Forest Cover Data Source Description")
    fcs_metadata = models.URLField(default="https://", help_text="Forest Cover Data Source Metadata URL")
    private = models.BooleanField(default=False, help_text="Private data source?")

    # Leave the user_id field out for now, but we will add it later
    # This will be a foreign key to the user table
    # user_id = models.CharField(max_length=100, default="", help_text="User ID")

    def __str__(self):
        return self.fcs_name

    def lc_label(self):
        return "fc" + self.id


class AGBSource(models.Model):
    agb_id = models.CharField(max_length=10, primary_key=True,
                              help_text="AGB ID number")
    agb_name = models.CharField(max_length=100, default="", help_text="AGB Label")
    agb_filename = models.CharField(max_length=100, default="", help_text="AGB File Name")

    def __str__(self):
        return self.agb_name

    def agb_label(self):
        return "AGB" + self.agb_id


class Emissions(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) - Let's use autogenerated IDs
    lc_id = models.ForeignKey(BoundaryFiles, default=1, verbose_name="LandCover", on_delete=models.SET_DEFAULT)
    agb_id = models.ForeignKey(AGBSource, default=1, verbose_name="AGB", on_delete=models.SET_DEFAULT)
    aoi_id = models.ForeignKey(AOI, default=1, verbose_name="AOI", on_delete=models.SET_DEFAULT)
    year = models.IntegerField(help_text="Year")
    baseline_year = models.IntegerField(help_text="Baseline Year for emissions calculations", blank=True, null=True)
    lc_agb_value = models.FloatField(help_text="Emissions")
    total_agb = models.FloatField(help_text='Total AGB', default=0.0)


class ForestCoverChangeNew(models.Model):
    fc_filename = models.CharField(max_length=100, default="", help_text="FC File")
    aoi = models.ForeignKey(AOI, default=1, help_text="AOI the calculation was made for", on_delete=models.CASCADE)
    year = models.IntegerField(help_text="Year the change was calculated for")
    baseline_year = models.IntegerField(help_text="Baseline Year for forest cover change calculation", blank=True,
                                        null=True)
    initial_forest_area = models.FloatField(help_text="Initial forest area for baseline year")
    forest_gain = models.FloatField(help_text="Forest Gain", null=True)
    forest_loss = models.FloatField(help_text="Forest Loss")
    processing_time = models.FloatField(
        help_text="Time to calculate forest change data for this time period, AOI and Forest Cover Change source (seconds)",
        blank=True, null=True)
    speedup = models.FloatField(help_text='New calculation speedup factor', blank=True, null=True)

    def net_forest_change(self):
        return self.forest_gain - self.forest_loss
