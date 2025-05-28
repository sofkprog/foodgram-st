from django.core.files.base import ContentFile
import base64
import imghdr
from rest_framework import serializers
from recipes.models import Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingCart
from api.users.serializers import UserListSerializer

MIN_AMOUNT = 1
MAX_AMOUNT = 32_000
MIN_VALUE = 1
MAX_VALUE = 32_000


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True, source="ingredient")
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount", "name", "measurement_unit")


class RecipeReadSerializer(serializers.ModelSerializer):
    class AuthorWithSubscriptionSerializer(UserListSerializer):
        is_subscribed = serializers.SerializerMethodField()

        class Meta(UserListSerializer.Meta):
            fields = UserListSerializer.Meta.fields + ("is_subscribed",)

        def get_is_subscribed(self, obj):
            request = self.context.get("request")
            user = request.user if request else None

            return False if not user or user.is_anonymous else False

    author = AuthorWithSubscriptionSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.is_favorited.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.is_in_shopping_cart.filter(user=user).exists()


class RecipeIngredientWriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=MIN_AMOUNT, max_value=MAX_AMOUNT)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True, required=True)
    image = serializers.CharField(write_only=True)
    name = serializers.CharField(
        max_length=256,
        required=True,
        allow_blank=False,
        error_messages={
            "blank": "Поле 'name' не может быть пустым.",
            "max_length": "Поле 'name' не может быть длиннее 256 символов.",
        },
    )
    text = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={"blank": "Поле 'text' не может быть пустым."},
    )
    cooking_time = serializers.IntegerField(
        required=True,
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
        error_messages={
            "min_value": "Время приготовления должно быть не меньше 1.",
            "required": "Поле 'cooking_time' обязательно.",
        },
    )

    class Meta:
        model = Recipe
        fields = ("ingredients", "image", "name", "text", "cooking_time")
        extra_kwargs = {
            "ingredients": {"required": True},
            "image": {"required": True},
            "name": {"required": True},
            "text": {"required": True},
            "cooking_time": {"required": True},
        }

    def validate(self, attrs):
        if self.instance and "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {
                    "ingredients": "Поле 'ingredients' обязательно при обновлении рецепта."
                }
            )
        return super().validate(attrs)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле 'ingredients' не может быть пустым."
            )

        ingredient_ids = [item["id"] for item in value]

        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")

        existing_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                "id", flat=True
            )
        )
        invalid_ids = set(ingredient_ids) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Ингредиенты с ID {list(invalid_ids)} не существуют."
            )

        return value

    def validate_image(self, value):
        if value.startswith("data:image"):
            try:
                value = value.split(";base64,")[1]
            except IndexError:
                raise serializers.ValidationError("Неверный формат base64 с префиксом.")
        try:
            decoded_file = base64.b64decode(value)
        except Exception:
            raise serializers.ValidationError("Неверный формат base64.")

        file_type = imghdr.what(None, decoded_file)
        if file_type not in ["jpeg", "png", "gif"]:
            raise serializers.ValidationError("Неподдерживаемый формат изображения.")
        return decoded_file

    def create_ingredients(self, recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=item["id"]),
                amount=item["amount"],
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        image_data = validated_data.pop("image")

        file_name = f'recipe_image_{validated_data.get("name", "noname")}.{imghdr.what(None, image_data)}'
        image_file = ContentFile(image_data, name=file_name)

        recipe = Recipe.objects.create(**validated_data, image=image_file)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        image_data = validated_data.pop("image", None)

        if ingredients_data is not None and len(ingredients_data) == 0:
            raise serializers.ValidationError(
                {"ingredients": "Поле 'ingredients' не может быть пустым."}
            )

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image_data:
            file_name = f"recipe_image_{instance.id}.{imghdr.what(None, image_data)}"
            instance.image.save(file_name, ContentFile(image_data), save=False)

        instance.save()

        if ingredients_data:
            instance.ingredients.clear()
            self.create_ingredients(instance, ingredients_data)

        return instance


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
