from datetime import datetime
from django.contrib.gis.db import models
from colorfield.fields import ColorField


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
    wdpaid = models.FloatField()
    wdpa_pid = models.CharField(max_length=52)
    pa_def = models.CharField(max_length=20)
    name = models.CharField(max_length=254)
    orig_name = models.CharField(max_length=254)
    desig = models.CharField(max_length=254, null=True)
    desig_eng = models.CharField(max_length=254, null=True)
    desig_type = models.CharField(max_length=20, null=True)
    iucn_cat = models.CharField(max_length=20)
    int_crit = models.CharField(max_length=100)
    marine = models.CharField(max_length=20)
    rep_m_area = models.FloatField()
    gis_m_area = models.FloatField()
    rep_area = models.FloatField()
    gis_area = models.FloatField()
    no_take = models.CharField(max_length=50)
    no_tk_area = models.FloatField()
    status = models.CharField(max_length=100)
    status_yr = models.IntegerField()
    gov_type = models.CharField(max_length=254)
    own_type = models.CharField(max_length=254)
    mang_auth = models.CharField(max_length=254)
    mang_plan = models.CharField(max_length=254)
    verif = models.CharField(max_length=20)
    metadataid = models.IntegerField()
    sub_loc = models.CharField(max_length=100)
    parent_iso = models.CharField(max_length=50)
    iso3 = models.CharField(max_length=50)
    supp_info = models.CharField(max_length=254)
    cons_obj = models.CharField(max_length=100, null=True)
    layer = models.CharField(max_length=254)
    path = models.CharField(max_length=254)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Predefined AOIs"


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


class NewCollection(models.Model):
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    collection_name = models.CharField(max_length=100, default="", help_text="Collection name")
    collection_description = models.CharField(max_length=100, default="", help_text="Collection Description")
    boundary_file = models.CharField(max_length=100, default="", help_text="Boundary File")
    tiff_file = models.CharField(max_length=100, default="", unique=True, help_text="Tiff file name")
    access_level = models.CharField(max_length=10, default="Public", help_text="Access Level")
    projection = models.CharField(max_length=100, default="", help_text="Projection")
    resolution = models.FloatField(max_length=100, default="", help_text="Resolution")
    username = models.CharField(max_length=100, default="", help_text="Username")
    path_to_tif_file = models.CharField(max_length=150, default="", help_text="Path to TIF location")
    path_to_boundary_file = models.CharField(max_length=150, default="", help_text="Path to Boundary file location")
    last_accessed_on = models.DateTimeField(default=datetime.now)


class UserProvidedAOI(models.Model):
    # Use autogenerated IDs (don't rely on a user defined a primary key)
    aoi_name = models.CharField(max_length=100, default="", unique=True, help_text="AOI name")
    aoi_shape_file = models.CharField(max_length=100, default="", help_text="AOI Shape file")
    path_to_aoi_file = models.CharField(max_length=150, default="", help_text="Path to Shape file location")
    username = models.CharField(max_length=100, default="", help_text="Username")
    last_accessed_on = models.DateTimeField(default=datetime.now)


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
