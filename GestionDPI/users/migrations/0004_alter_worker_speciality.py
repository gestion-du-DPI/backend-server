# Generated by Django 5.1.4 on 2024-12-29 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_patient_date_of_birth_remove_patient_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='worker',
            name='speciality',
            field=models.CharField(max_length=50),
        ),
    ]
