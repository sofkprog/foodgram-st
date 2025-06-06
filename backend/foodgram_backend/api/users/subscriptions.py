from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import serializers, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from users.models import CustomUser, Subscription
from recipes.models import Recipe


class RecipeShortSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        request = self.context["request"]
        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class SubscriptionUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return obj.following.filter(user=user).exists()

    def get_recipes(self, obj):
        request = self.context["request"]
        recipes_limit = request.query_params.get("recipes_limit")
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[: int(recipes_limit)]
            except ValueError:
                pass
        return RecipeShortSerializer(
            recipes, many=True, context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar:
            url = obj.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("user", "author")

    def validate(self, data):
        if data["user"] == data["author"]:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        if data["author"].following.filter(user=data["user"]).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return data


class CustomPagination(PageNumberPagination):
    page_size_query_param = "limit"


class SubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        return CustomUser.objects.filter(following__user=self.request.user)


class SubscribeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        user = request.user
        author = get_object_or_404(CustomUser, id=id)
        serializer = SubscriptionCreateSerializer(
            data={"user": user.id, "author": author.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = SubscriptionUserSerializer(
            author, context={"request": request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = request.user
        author = get_object_or_404(CustomUser, id=id)
        subscription = user.follower.filter(author=author)

        if not subscription.exists():
            return Response(
                {"errors": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
