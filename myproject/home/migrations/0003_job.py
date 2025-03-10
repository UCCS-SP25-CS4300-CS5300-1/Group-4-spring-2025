# Generated by Django 5.1.7 on 2025-03-10 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_application_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('industry', models.CharField(blank=True, max_length=100, null=True)),
                ('location', models.CharField(blank=True, max_length=100, null=True)),
                ('is_remote', models.BooleanField(default=False)),
                ('salary_min', models.IntegerField(blank=True, null=True)),
                ('salary_max', models.IntegerField(blank=True, null=True)),
            ],
        ),
    ]
