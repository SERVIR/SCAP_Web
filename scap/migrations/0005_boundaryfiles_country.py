# Generated by Django 4.1 on 2023-08-28 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scap', '0004_alter_boundaryfiles_nomemun'),
    ]

    operations = [
        migrations.AddField(
            model_name='boundaryfiles',
            name='country',
            field=models.CharField(default='CY', max_length=2),
            preserve_default=False,
        ),
    ]
