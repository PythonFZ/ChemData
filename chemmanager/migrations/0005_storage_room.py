# Generated by Django 3.0.4 on 2020-03-06 11:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemmanager', '0004_auto_20200306_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='storage',
            name='room',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]