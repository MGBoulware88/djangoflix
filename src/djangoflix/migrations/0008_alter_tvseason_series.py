# Generated by Django 5.2.1 on 2025-05-23 22:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djangoflix', '0007_remove_watchablecontent_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tvseason',
            name='series',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='djangoflix.watchablecontent'),
        ),
    ]
