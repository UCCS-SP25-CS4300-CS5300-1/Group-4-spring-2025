# Generated by Django 4.2.20 on 2025-04-08 04:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_alter_joblisting_options_and_more'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='joblisting',
            name='home_joblis_search__80685b_idx',
        ),
        migrations.RemoveField(
            model_name='joblisting',
            name='cached_at',
        ),
        migrations.AddIndex(
            model_name='joblisting',
            index=models.Index(fields=['search_key'], name='home_joblis_search__ead644_idx'),
        ),
    ]
