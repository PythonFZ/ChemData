# Generated by Django 3.0.4 on 2020-03-06 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemmanager', '0002_auto_20200305_1516'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chemical',
            name='image',
            field=models.ImageField(default='profile_pics/default.png', upload_to='chemical_pics'),
        ),
    ]