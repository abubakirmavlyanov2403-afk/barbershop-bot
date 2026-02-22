from django.db import models
from appointments.models import Appointment

class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review', verbose_name='Запись')
    rating = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)], verbose_name='Оценка')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отзыва')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"Отзыв #{self.id} - {self.rating}★"