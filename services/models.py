from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название категории')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок сортировки')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order']

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название услуги')
    description = models.TextField(blank=True, verbose_name='Описание')
    duration = models.PositiveIntegerField(verbose_name='Длительность (мин)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена (руб)')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Категория')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    image = models.ImageField(upload_to='services/', blank=True, null=True, verbose_name='Изображение')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return f"{self.name} - {self.price} ₽"