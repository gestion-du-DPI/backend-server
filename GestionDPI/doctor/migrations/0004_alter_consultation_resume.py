# Generated by Django 5.1.4 on 2024-12-29 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0003_remove_labobservation_bilan_remove_labimage_bilan_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consultation',
            name='resume',
            field=models.TextField(blank=True, null=True),
        ),
    ]
