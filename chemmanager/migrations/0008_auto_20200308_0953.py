# Generated by Django 3.0.4 on 2020-03-08 08:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chemmanager', '0007_auto_20200308_0943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='chemical',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='chemmanager.Chemical'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='stock',
            name='storage',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='chemmanager.Storage'),
            preserve_default=False,
        ),
    ]