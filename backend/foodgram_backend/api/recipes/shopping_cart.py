from rest_framework import serializers, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, ShoppingCart


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


@api_view(["POST", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def manage_shopping_cart(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if request.method == "POST":
        if request.user.shopping_cart.filter(recipe=recipe).exists():
            return Response(
                {"errors": "Рецепт уже в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if request.method == "DELETE":
        cart_item = request.user.shopping_cart.filter(recipe=recipe)
        if not cart_item.exists():
            return Response(
                {"errors": "Рецепта нет в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
