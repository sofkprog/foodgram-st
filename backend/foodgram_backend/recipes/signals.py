import json
import os
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.files import File

from .models import Recipe, Ingredient, RecipeIngredient
from django.contrib.auth import get_user_model

User = get_user_model()
@receiver(post_migrate)
def load_test_data(sender, **kwargs):
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

@receiver(post_migrate)
def create_initial_recipes(sender, **kwargs):
    json_path = os.path.join(settings.BASE_DIR, 'data', 'recipes.json')
    if not os.path.exists(json_path):
        return

    with open(json_path, encoding='utf-8') as file:
        recipes_data = json.load(file)

    for recipe_data in recipes_data:
        author_id = recipe_data["author_id"]
        try:
            author = User.objects.get(id=author_id)
        except User.DoesNotExist:
            continue

        if Recipe.objects.filter(name=recipe_data["name"], author=author).exists():
            continue

        recipe = Recipe(
            author=author,
            name=recipe_data["name"],
            text=recipe_data["text"],
            cooking_time=recipe_data["cooking_time"],
        )

        image_path = os.path.join(settings.BASE_DIR, 'media', 'recipes', 'images', recipe_data["image"])
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                django_file = File(img_file)
                recipe.image.save(os.path.basename(image_path), django_file, save=False)

        recipe.save()  # сохраняем объект после присвоения изображения

        for ing_data in recipe_data["ingredients"]:
            try:
                ingredient = Ingredient.objects.get(name=ing_data["name"])
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ing_data["amount"]
                )
            except Ingredient.DoesNotExist:
                print(f"⚠ Ingredient {ing_data['name']} not found, skipped.")

        print(f"✅ Recipe '{recipe.name}' created.")