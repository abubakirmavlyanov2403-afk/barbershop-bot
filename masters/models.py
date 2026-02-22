from django.db import models
from users.models import User
from services.models import Service

class Master(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'master'}, verbose_name='Пользователь')
    services = models.ManyToManyField(Service, related_name='masters', verbose_name='Услуги')
    experience = models.PositiveIntegerField(verbose_name='Опыт работы (лет)')
    bio = models.TextField(blank=True, verbose_name='О себе')
    rating = models.FloatField(default=0.0, verbose_name='Рейтинг')
    reviews_count = models.PositiveIntegerField(default=0, verbose_name='Количество отзывов')
    is_available = models.BooleanField(default=True, verbose_name='Доступен')

    class Meta:
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'

    def __str__(self):
        return self.user.get_full_name()