from rest_framework import viewsets, status, filters, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Recipe, Ingredient, ShoppingCart, RecipeIngredient
from .serializers import (
    RecipeReadSerializer,
    RecipeWriteSerializer,
    IngredientSerializer,
)
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django.http import HttpResponse
from .models import Favorite
from .serializers import FavoriteRecipeSerializer


class NoPagination(PageNumberPagination):
    page_size = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = NoPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name")
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["author"]
    search_fields = ["name"]

    def get_object(self):
        obj = super().get_object()
        if self.request.method not in permissions.SAFE_METHODS:
            if obj.author != self.request.user:
                raise PermissionDenied("Вы не являетесь автором этого рецепта.")
        return obj

    def get_serializer_class(self):
        if self.request.method in ["GET"]:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = RecipeReadSerializer(
            serializer.instance, context={"request": request}
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = RecipeReadSerializer(
            serializer.instance, context={"request": request}
        )
        return Response(read_serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = {}

        cart_items = ShoppingCart.objects.filter(user=request.user).select_related(
            "recipe"
        )
        for item in cart_items:
            recipe_ingredients = RecipeIngredient.objects.filter(
                recipe=item.recipe
            ).select_related("ingredient")
            for ri in recipe_ingredients:
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                key = f"{name} ({unit})"
                ingredients[key] = ingredients.get(key, 0) + ri.amount

        lines = [f"{name} — {amount}" for name, amount in ingredients.items()]
        content = "\n".join(lines)

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        if request.method == "POST":
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = FavoriteRecipeSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"errors": "Рецепт не найден в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user

        is_favorited = self.request.query_params.get("is_favorited")
        is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart")

        if is_favorited == "1":
            if user.is_authenticated:
                queryset = queryset.filter(is_favorited__user=user)
            else:
                return Recipe.objects.none()
        elif is_favorited == "0":
            pass

        if is_in_shopping_cart == "1":
            if user.is_authenticated:
                queryset = queryset.filter(is_in_shopping_cart__user=user)
            else:
                return Recipe.objects.none()
        elif is_in_shopping_cart == "0":
            pass

        return queryset

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link = request.build_absolute_uri(f"/recipes/{recipe.id}/")
        return Response({"short-link": link})
