from django.contrib import admin
from .models import Master

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience', 'rating', 'is_available')
    list_filter = ('is_available', 'services')
    filter_horizontal = ('services',)