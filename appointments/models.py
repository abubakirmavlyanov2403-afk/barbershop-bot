from django.db import models
from users.models import User
from masters.models import Master
from services.models import Service

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидание'),
        ('confirmed', 'Подтверждено'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
        ('no_show', 'Не пришел'),
    )
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', limit_choices_to={'user_type':'client'}, verbose_name='Клиент')
    master = models.ForeignKey(Master, on_delete=models.CASCADE, verbose_name='Мастер')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Услуга')
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    reminder_sent = models.BooleanField(default=False, verbose_name='Напоминание отправлено')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-date', '-time']
        indexes = [models.Index(fields=['date', 'status'])]

    def __str__(self):
        return f"{self.client} - {self.service} - {self.date} {self.time}"