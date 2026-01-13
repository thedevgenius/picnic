from django.db import models
from django.contrib.auth.models import (
    AbstractUser, PermissionsMixin, BaseUserManager
)
from django.contrib.auth.hashers import make_password, identify_hasher
import uuid
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    username = None
    phone = models.CharField(max_length=15, unique=True, db_index=True)
    candidate = models.IntegerField(default=1)
    
    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

class OneTimeLoginToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (not self.is_used) and timezone.now() < self.expires_at

    @staticmethod
    def create_token(user, minutes=10):
        return OneTimeLoginToken.objects.create(
            user=user,
            expires_at=timezone.now() + timedelta(minutes=minutes)
        )

class Diposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount}"

