from django.contrib.auth.models import AbstractUser
from django.db import models


def user_avatar_upload_path(instance, filename):
    return f"users/avatars/{instance.username}/{filename}"


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to=user_avatar_upload_path, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        CustomUser,
        related_name="follower",
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        CustomUser,
        related_name="following",
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_subscription"
            )
        ]
        ordering = ["id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
