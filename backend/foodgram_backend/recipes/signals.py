import json
import os

from django.conf import settings
from django.core.files import File
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Ingredient

@receiver(post_migrate)
def load_test_data(sender, **kwargs):
    # Загрузка ингредиентов
    if not Ingredient.objects.exists():
        try:
            file_path = os.path.join(settings.BASE_DIR, 'data', 'ingredients.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for item in data:
                Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
            print("Ингредиенты успешно загружены из файла.")
        except Exception as e:
            print(f"Ошибка при загрузке ингредиентов: {e}")