# Generated by Django 5.1.4 on 2024-12-29 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='nss',
            field=models.CharField(default=222, max_length=50, unique=True),
            preserve_default=False,
        ),
    ]
