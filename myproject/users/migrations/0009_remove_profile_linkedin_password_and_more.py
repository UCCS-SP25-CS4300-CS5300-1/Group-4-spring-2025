# Generated by Django 4.2.20 on 2025-04-08 04:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_resume_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='linkedIn_password',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='linkedIn_username',
        ),
    ]
