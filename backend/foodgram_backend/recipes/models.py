from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000

MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000


class Ingredient(models.Model):
    name = models.CharField(max_length=256, verbose_name="Название ингредиента")
    measurement_unit = models.CharField(max_length=64, verbose_name="Единица измерения")

    class Meta:
        ordering = ["id"]
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes", verbose_name="Автор"
    )
    name = models.CharField(max_length=256, verbose_name="Название рецепта")
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Изображение")
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
        verbose_name="Время приготовления (мин)",
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингредиенты"
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ],
        verbose_name="Количество",
    )

    class Meta:
        unique_together = ("recipe", "ingredient")
        ordering = ["id"]
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецепте"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="is_in_shopping_cart",
        verbose_name="Рецепт",
    )

    class Meta:
        unique_together = ("user", "recipe")
        ordering = ["id"]
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        related_name="is_favorited",
        verbose_name="Рецепт",
    )

    class Meta:
        unique_together = ("user", "recipe")
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        ordering = ["id"]
