from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email", "name", "password"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5, "required": False}}
        # read_only = ["password"]

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        # or
        # return get_user_model().objects.create_user(**validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        user = authenticate(
            request=self.context["request"],
            username=attrs["email"],
            password=attrs["password"],
        )

        if not user:
            msg = "ایمیل یا پسورد وارد شده صحیح نمیباشد."
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs
