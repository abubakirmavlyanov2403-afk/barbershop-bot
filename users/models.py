from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    USER_TYPES = (
        ('client', 'Клиент'),
        ('master', 'Мастер'),
        ('admin', 'Администратор'),
        ('owner', 'Владелец'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client', verbose_name='Тип пользователя')
    phone_regex = RegexValidator(regex=r'^\+7\d{10}$', message="Телефонный номер должен начинаться с +7 и содержать 10 цифр.")
    phone = models.CharField(validators=[phone_regex], max_length=12, unique=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    telegram_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='Telegram ID')
    vk_id = models.CharField(max_length=100, blank=True, null=True, verbose_name='VK ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone})"