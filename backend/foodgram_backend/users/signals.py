import json
import os
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_migrate)
def create_initial_users(sender, **kwargs):
    json_path = os.path.join(settings.BASE_DIR, "data", "users.json")
    if not os.path.exists(json_path):
        return

    with open(json_path, encoding="utf-8") as file:
        users_data = json.load(file)

    for user_data in users_data:
        if not User.objects.filter(email=user_data["email"]).exists():
            user = User.objects.create_user(
                email=user_data["email"],
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password=user_data["password"],
            )
            print(f"Created user: {user.email}")
