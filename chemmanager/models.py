from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from users.models import Workgroup


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
    workgroup = models.ForeignKey(Workgroup, on_delete=models.CASCADE, blank=True, null=True)

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


class Storage(models.Model):
    name = models.CharField(max_length=250)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    workgroup = models.ManyToManyField(Workgroup)

    def __str__(self):
        return self.name


class Stock(models.Model):

    name = models.CharField(max_length=250)

    quantity = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_changed = models.DateTimeField(auto_now=True)

    chemical = models.ForeignKey(Chemical, on_delete=models.CASCADE, blank=True, null=True)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def left_quantity(self):
        left_quantity = self.quantity
        for extraction in self.extraction_set.all():
            left_quantity -= extraction.quantity

        return left_quantity

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_changed']

    def get_absolute_url(self):
        url = reverse('chemmanager-home') + '?q=' + self.chemical.name
        return url


class Extraction(models.Model):
    # TODO different Units interconversion
    quantity = models.FloatField()
    date_created = models.DateTimeField(default=timezone.now)
    comment = models.TextField(blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    def get_absolute_url(self):
        url = reverse('chemmanager-home') + '?q=' + self.stock.chemical.name
        return url

    class Meta:
        ordering = ['-date_created']


