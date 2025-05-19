from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from .models import CustomUser
import base64
import imghdr
from django.contrib.auth import authenticate


class UserListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "first_name", "last_name", "avatar")

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar:
            url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    id = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = CustomUser
        fields = ("email", "username", "first_name", "last_name", "password", "id")

    def create(self, validated_data):
        user = CustomUser.objects.create(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
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
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        from .subscriptions import Subscription

        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar:
            url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField(write_only=True)

    def validate_avatar(self, value):
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

    def update(self, instance, validated_data):
        avatar_data = validated_data.get("avatar")

        file_name = f"user_{instance.id}_avatar.{imghdr.what(None, avatar_data)}"
        instance.avatar.save(file_name, ContentFile(avatar_data), save=True)
        return instance

    def create(self, validated_data):

        raise NotImplementedError("Create не поддерживается для AvatarSerializer")


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Email", write_only=True)
    password = serializers.CharField(
        label="Password",
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label="Token", read_only=True)
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), email=email, password=password
            )

            if not user:
                raise serializers.ValidationError(
                    "Неверные учетные данные для входа.", code="authorization"
                )
        else:
            raise serializers.ValidationError(
                "Email и пароль обязательны.", code="authorization"
            )

        attrs["user"] = user
        return attrs
