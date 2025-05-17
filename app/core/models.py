from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,

)
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("ایمیل نمیتواند خالی باشد.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        max_length=255,
        unique=True,
        verbose_name="ایمیل"
    )
    name = models.CharField(max_length=255, verbose_name="نام")
    is_active = models.BooleanField(default=True, verbose_name="کاربر فعال")
    is_staff = models.BooleanField(default=False, verbose_name="کاربر مدیر")

    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربر"


class Recipe(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="قیمت"
    )
    time_minutes = models.IntegerField(verbose_name="مدت")
    link = models.CharField(max_length=255, blank=True, verbose_name="لینک")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )
    tags = models.ManyToManyField('Tag', verbose_name="تگ")
    ingredients = models.ManyToManyField(
        'Ingredient',
        verbose_name="مواد اولیه"
    )

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )

    def __str__(self):
        return self.name
