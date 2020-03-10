from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from users.models import Workgroup
from treebeard.mp_tree import MP_Node
from django.utils.safestring import mark_safe
from PIL import Image


class Chemical(models.Model):

    name = models.CharField(max_length=250)
    structure = models.CharField(max_length=250, blank=True, null=True)
    molar_mass = models.FloatField(blank=True, null=True)
    density = models.FloatField(blank=True, null=True)
    melting_point = models.FloatField(blank=True, null=True)
    boiling_point = models.FloatField(blank=True, null=True)

    comment = models.TextField(blank=True)
    cid = models.CharField(max_length=100, blank=True, null=True)
    cas = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='chemical_pics', blank=True, null=True)

    secret = models.BooleanField(blank=True, null=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    workgroup = models.ForeignKey(Workgroup, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        url = reverse('chemical-list', kwargs={'pk': self.pk}) + '?q=' + self.name
        return url

    @property
    def allowed_edit(self):
        return [self.creator]

    def test_func_1(self):
        return self.stock_set.first().name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            with Image.open(self.image.path) as img:
                if img.height > 250 or img.width > 250:
                    output_size = (250, 250)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
        except ValueError:
            print('No Image found')


class Unit(models.Model):
    name = models.CharField(max_length=100)

    equals_standard = models.FloatField(blank=True, null=True)
    equals_standard_unit = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name


class Storage(MP_Node):
    name = models.CharField(max_length=250)
    room = models.CharField(max_length=100, blank=True, null=True)
    abbreviation = models.CharField(max_length=3, blank=True, null=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    workgroup = models.ManyToManyField(Workgroup)

    node_order_by = ['name']

    def __unicode__(self):
        return f'Place: {self.name}'

    @property
    def location_name(self):
        '''Display Name like Place A (Subplace B, detailed Place C) in ListView'''
        if self.get_depth() > 1:
            name_str = self.get_root().name + ' ('
            for parent in self.get_ancestors()[1:]:
                name_str += f'{parent.name}, '
            name_str += f'{self.name})'
            return name_str
        else:
            return self.name

    @property
    def full_abbr(self):
        my_abbr = ''
        for ancestor in self.get_ancestors():
            my_abbr += ancestor.abbreviation
        if self.abbreviation:
            my_abbr += self.abbreviation
        return my_abbr

    def __str__(self):
        if self.workgroup.count() > 1:
            return mark_safe('&nbsp;&nbsp;' * (self.get_depth()-1) + self.name + ' (shared)')
        else:
            str = '&nbsp;&nbsp;' * (self.get_depth()-1) + self.name
            if self.abbreviation:
                str += f'({self.abbreviation})'
            # Intended to show Tree-View like behaviour
            return mark_safe(str)


class Stock(models.Model):

    name = models.CharField(max_length=250)

    quantity = models.FloatField()
    comment = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_changed = models.DateTimeField(auto_now=True)

    label = models.CharField(max_length=10, blank=True, null=True)

    chemical = models.ForeignKey(Chemical, on_delete=models.CASCADE,)
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE,)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)

    @property
    def left_quantity(self):
        if self.unit:
            left_quantity = self.quantity
            for extraction in self.extraction_set.all():
                left_quantity -= self.unit_converter(extraction)

            return left_quantity
        else:
            'ERROR'

    def unit_converter(self, extraction):
        """
        Check unit and compare with Stock Unit, if different, try to convert:
        """
        # Has to be written twice, can otherwise not be imported
        unit = extraction.unit
        stock_unit = self.unit
        if unit == stock_unit:
            return extraction.quantity
        else:
            fact = 1
            if stock_unit != stock_unit.equals_standard_unit:
                fact /= stock_unit.equals_standard
                stock_unit = stock_unit.equals_standard_unit

            if unit.equals_standard_unit == stock_unit:
                return extraction.quantity * unit.equals_standard * fact
            else:
                return 0

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_changed']

    def get_absolute_url(self):
        url = reverse('chemical-list', kwargs={'pk': self.chemical.pk}) + '?q=' + self.chemical.name
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


