# Generated by Django 5.2.1 on 2025-05-23 22:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djangoflix', '0009_tvepisode_tmdb_id_tvseason_tmdb_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tvepisode',
            name='season',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='djangoflix.tvseason'),
        ),
    ]
