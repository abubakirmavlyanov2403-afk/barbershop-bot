from django.db import models
from users.models import User

class Notification(models.Model):
    TYPE_CHOICES = (('reminder','Напоминание'),('confirmation','Подтверждение'),('promo','Акция'),('subscription','Абонемент'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Тип')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')
    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name='Запланировано на')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"