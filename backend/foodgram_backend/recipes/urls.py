from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.recipes.views import RecipeViewSet, IngredientViewSet
from api.recipes.shopping_cart import manage_shopping_cart

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path("recipes/<int:recipe_id>/shopping_cart/", manage_shopping_cart),
]
