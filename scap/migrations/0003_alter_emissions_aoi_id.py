# Generated by Django 4.1 on 2024-01-31 18:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('scap', '0002_agbsource_forestcoversource_emissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emissions',
            name='aoi_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='scap.aoi',
                                    verbose_name='AOI'),
        ),
    ]