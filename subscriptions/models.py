from django.db import models
from users.models import User
from services.models import Service

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название абонемента')
    services = models.ManyToManyField(Service, verbose_name='Услуги')
    visits_total = models.PositiveIntegerField(verbose_name='Количество посещений')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена (руб)')
    duration_days = models.PositiveIntegerField(verbose_name='Срок действия (дней)')
    max_freeze_days = models.PositiveIntegerField(default=0, verbose_name='Макс. дней заморозки')
    available_days = models.CharField(max_length=100, blank=True, verbose_name='Доступные дни')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'План абонемента'
        verbose_name_plural = 'Планы абонементов'

    def __str__(self):
        return f"{self.name} - {self.price} ₽"

class Subscription(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, verbose_name='План')
    visits_used = models.PositiveIntegerField(default=0, verbose_name='Использовано посещений')
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Оплаченная сумма')
    valid_from = models.DateField(verbose_name='Действует с')
    valid_until = models.DateField(verbose_name='Действует до')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    frozen_until = models.DateField(null=True, blank=True, verbose_name='Заморожен до')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')

    class Meta:
        verbose_name = 'Абонемент клиента'
        verbose_name_plural = 'Абонементы клиентов'

    def remaining_visits(self):
        return self.plan.visits_total - self.visits_used