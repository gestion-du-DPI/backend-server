# Generated by Django 5.1.4 on 2024-12-28 16:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='consultation',
            old_name='date',
            new_name='created_at',
        ),
    ]
