from django.contrib import admin
from .models import Chemical, Stock, Unit, Storage


admin.site.register(Chemical)
admin.site.register(Stock)
admin.site.register(Unit)
admin.site.register(Storage)