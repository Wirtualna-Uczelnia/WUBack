# Generated by Django 3.1.4 on 2020-12-19 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usersauth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='wu_user',
            name='first_name',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='wu_user',
            name='lastname',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
