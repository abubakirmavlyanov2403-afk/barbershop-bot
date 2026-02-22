from django.db import models
from masters.models import Master

class Schedule(models.Model):
    DAYS_OF_WEEK = ((0,'Пн'),(1,'Вт'),(2,'Ср'),(3,'Чт'),(4,'Пт'),(5,'Сб'),(6,'Вс'))
    master = models.ForeignKey(Master, on_delete=models.CASCADE, related_name='schedules', verbose_name='Мастер')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name='День недели')
    start_time = models.TimeField(verbose_name='Начало работы')
    end_time = models.TimeField(verbose_name='Конец работы')
    break_start = models.TimeField(null=True, blank=True, verbose_name='Начало перерыва')
    break_end = models.TimeField(null=True, blank=True, verbose_name='Конец перерыва')

    class Meta:
        unique_together = ('master', 'day_of_week')
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'

    def __str__(self):
        return f"{self.master} - {self.get_day_of_week_display()}: {self.start_time}-{self.end_time}"