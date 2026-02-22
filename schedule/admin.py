from django.contrib import admin
from .models import Schedule

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('master', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('master', 'day_of_week')