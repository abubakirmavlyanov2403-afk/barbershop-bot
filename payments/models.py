from django.db import models
from appointments.models import Appointment

class Payment(models.Model):
    PAYMENT_METHODS = (('cash','Наличные'),('card','Карта'),('yookassa','ЮKassa'),('sbp','СБП'),('tinkoff','Тинькофф'))
    STATUS_CHOICES = (('pending','Ожидание'),('paid','Оплачено'),('failed','Ошибка'),('refunded','Возврат'))
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='payment', verbose_name='Запись')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма (руб)')
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='Способ оплаты')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    transaction_id = models.CharField(max_length=200, blank=True, verbose_name='ID транзакции')
    payment_url = models.URLField(blank=True, verbose_name='Ссылка на оплату')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return f"Платеж #{self.id} - {self.amount} руб."