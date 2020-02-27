from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect


class Chemical(models.Model):

    name = models.CharField(max_length=250)
    structure = models.CharField(max_length=250, blank=True)
    molar_mass = models.FloatField(blank=True, null=True)
    density = models.FloatField(blank=True, null=True)
    melting_point = models.FloatField(blank=True, null=True)
    boiling_point = models.FloatField(blank=True, null=True)

    comment = models.TextField(blank=True)
    cid = models.CharField(max_length=100, blank=True, null=True)
    cas = models.CharField(max_length=100, blank=True, null=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        url = reverse('chemmanager-home') + '?q=' + self.name
        return url
        # return reverse('chemical-detail', kwargs={'pk': self.pk})


class Unit(models.Model):
    name = models.CharField(max_length=100)

    equals_standard = models.CharField(max_length=100, blank=True, null=True)
    equals_standard_unit = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


class Stock(models.Model):

    name = models.CharField(max_length=250)

    quantity = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_changed = models.DateTimeField(auto_now=True)

    chemical = models.ForeignKey(Chemical, on_delete=models.CASCADE, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('stock-detail', kwargs={'pk': self.pk})
