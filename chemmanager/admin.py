from django.contrib import admin
from .models import Chemical, Stock, Unit

admin.site.register(Chemical)
admin.site.register(Stock)
admin.site.register(Unit)