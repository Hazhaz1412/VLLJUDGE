# Generated by Django 5.1.4 on 2025-01-06 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='memory_limit',
            field=models.IntegerField(default=256),
        ),
        migrations.AddField(
            model_name='problem',
            name='time_limit',
            field=models.IntegerField(default=1),
        ),
    ]
