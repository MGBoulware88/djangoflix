# Generated by Django 5.2.1 on 2025-05-21 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tmdb', '0003_remove_tmdbmovie_img_path_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tmdbmovie',
            old_name='img_fetch_path',
            new_name='img_path',
        ),
        migrations.RenameField(
            model_name='tmdbtvepisode',
            old_name='img_fetch_path',
            new_name='img_path',
        ),
        migrations.RenameField(
            model_name='tmdbtvseason',
            old_name='img_fetch_path',
            new_name='img_path',
        ),
        migrations.RenameField(
            model_name='tmdbtvseries',
            old_name='img_fetch_path',
            new_name='img_path',
        ),
    ]
