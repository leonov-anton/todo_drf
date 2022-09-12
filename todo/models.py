from django.db import models


class Task(models.Model):
    PRIORITY_CHOICES = [('high', 'high'), ('normal', 'normal'), ('low', 'low')]

    title = models.CharField(max_length=100, verbose_name='Название')
    content = models.TextField(blank=True, verbose_name='Описание')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    deadline = models.DateTimeField(verbose_name='Дедлайн')
    done_time = models.DateTimeField(null=True, verbose_name='Дата и время завершения')
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, default=None, verbose_name='Создал')
    status = models.BooleanField(default=False, verbose_name='Статус')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name='Приоритет')
    category = models.ForeignKey('Category', null=True, on_delete=models.PROTECT, verbose_name='Категория')

    class Meta:
        verbose_name_plural = 'Задачи'
        verbose_name = 'Задача'
        ordering = ['deadline']


class Category(models.Model):
    name = models.CharField(max_length=20, verbose_name='Название категории')
    user = models.ManyToManyField('auth.User', default=None, verbose_name='Пользователи категории')

    class Meta:
        verbose_name_plural = 'Категории'
        verbose_name = 'Категория'
        ordering = ['name']
