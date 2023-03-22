from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель для учетных записей пользователей"""
    USER = 'user'
    ADMIN = 'admin'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password',)

    ROLE_CHOICES = [
        (USER, USER),
        (ADMIN, ADMIN),
    ]
    role = models.CharField(
        'Role',
        max_length=255,
        choices=ROLE_CHOICES,
        default=USER,
        blank=True
    )

    email = models.EmailField(
        verbose_name='Эл.почта',
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Имя учетной записи пользователя',
        max_length=150,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
        blank=False,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
        blank=False,
    )
    password = models.CharField(
        verbose_name='Пароль',
        max_length=150,
    )

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username
